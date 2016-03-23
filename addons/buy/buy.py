# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016  开阖软件(<http://www.osbzr.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api
from openerp.exceptions import except_orm

BUY_ORDER_STATES = [
        ('draft', u'草稿'),
        ('approved', u'已审核'),
        ('confirmed', u'未入库'),
        ('part_in', u'部分入库'),
        ('all_in', u'全部入库'),
    ]
BUY_RECEIPT_STATES = [
        ('draft', u'草稿'),
        ('approved', u'已审核'),
        ('confirmed', u'未付款'),
        ('part_paid', u'部分付款'),
        ('paid', u'全部付款'),
    ]
READONLY_STATES = {
        'approved': [('readonly', True)],
        'confirmed': [('readonly', True)],
    }
class buy_order(models.Model):
    _name = "buy.order"
    _inherit = ['mail.thread']
    _description = u"采购订单"
    _order = 'date desc, id desc'

    @api.one
    @api.depends('line_ids.subtotal', 'discount_rate')
    def _compute_amount(self):
        '''计算订单合计金额，并且当优惠率改变时，改变优惠金额和优惠后金额'''
        self.total = sum(line.subtotal for line in self.line_ids)
        self.discount_amount = self.total * self.discount_rate * 0.01
        self.amount = self.total - self.discount_amount

    partner_id = fields.Many2one('partner', u'供应商', required=True, states=READONLY_STATES)
    date = fields.Date(u'单据日期', states=READONLY_STATES, default=lambda self: fields.Date.context_today(self),
            select=True, help=u"默认是订单创建日期", copy=False)
    planned_date = fields.Date(u'交货日期', states=READONLY_STATES, default=lambda self: fields.Date.context_today(self), select=True, help=u"订单的预计交货日期")
    name = fields.Char(u'单据编号', required=True, select=True, copy=False,
        default='/', help=u"采购订单的唯一编号，当创建时它会自动生成有序编号。")
    type = fields.Selection([('buy', u'购货'),('return', u'退货')], u'类型', default='buy')
    line_ids = fields.One2many('buy.order.line', 'order_id', u'采购订单行', states=READONLY_STATES, copy=True)
    note = fields.Text(u'备注', states=READONLY_STATES)
    total = fields.Float(string=u'合计', store=True,readonly=True,
            compute='_compute_amount', track_visibility='always', help=u'所有订单行小计之和')
    discount_rate = fields.Float(u'优惠率(%)', states=READONLY_STATES)
    discount_amount = fields.Float(string=u'优惠金额', store=True, states=READONLY_STATES,
            compute='_compute_amount', track_visibility='always')
    amount = fields.Float(string=u'优惠后金额', store=True,readonly=True,
            compute='_compute_amount', track_visibility='always')
    approve_uid = fields.Many2one('res.users', u'审核人', copy=False)
    state = fields.Selection(BUY_ORDER_STATES, u'订单状态', readonly=True, help=u"采购订单的状态", select=True, copy=False, default='draft')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', '采购订单号必须唯一!'),
    ]

    @api.model
    def create(self, vals):
        if not vals.get('line_ids'):
            raise except_orm(u'警告！', u'请输入产品明细行！')
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get(self._name) or '/'
        return super(buy_order, self).create(vals)

    @api.one
    def buy_approve(self):
        '''审核购货订单'''
        self.write({'state': 'approved', 'approve_uid': self._uid})
        return True

    @api.one
    def buy_refuse(self):
        '''反审核购货订单'''
        if self.state == 'confirmed':
            raise except_orm(u'警告！', u'该单据已经生成了关联单据，不能反审核！')
        self.write({'state': 'draft', 'approve_uid': ''})
        return True

    @api.one
    def buy_generate_order(self):
        '''由购货订单生成采购入库单'''
        dict = []
        ret = []

        for line in self.line_ids:
            # 如果订单部分入库，则点击此按钮时生成剩余数量的入库单
            goods_qty = line.quantity
            qty = 0
            if self.state == 'part_in':
                for order in self.env['buy.receipt'].search([('origin', '=', self.name), ('state', '!=', 'draft')]):
                    for line_in in order.line_in_ids:
                        if line.goods_id == line_in.goods_id:
                            qty += line_in.goods_qty
                goods_qty = line.quantity - qty
            dict.append({
                'goods_id': line.goods_id and line.goods_id.id or '',
                'spec': line.spec,
                'uom_id': line.uom_id.id,
                'warehouse_id': line.warehouse_id and line.warehouse_id.id or '',
                'warehouse_dest_id': line.warehouse_dest_id and line.warehouse_dest_id.id or '',
                'goods_qty': goods_qty,
                'price': line.price,
                'discount_rate': line.discount_rate,
                'discount': line.discount,
                'amount': line.amount,
                'tax_rate': line.tax_rate,
                'tax_amount': line.tax_amount,
                'subtotal': line.subtotal or 0.0,
                'note': line.note or '',
                'share_cost': 0,
            })

        for i in range(len(dict)):
            ret.append((0, 0, dict[i]))
        receipt_id = self.env['buy.receipt'].create({
                            'partner_id': self.partner_id.id,
                            'date': fields.Date.context_today(self),
                            'origin': self.name,
                            'line_in_ids': ret,
                            'note': self.note,
                            'discount_rate': self.discount_rate,
                            'discount_amount': self.discount_amount,
                            'amount': self.amount,
                            'state': 'draft',
                        })
        view_id = self.env['ir.model.data'].xmlid_to_res_id('buy.buy_receipt_form')
        self.write({'state': 'confirmed'})
        return {
            'name': u'采购入库单',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(view_id, 'form')],
            'res_model': 'buy.receipt',
            'type': 'ir.actions.act_window',
            'domain':[('id', '=', receipt_id)],
            'target': 'current',
        }

class buy_order_line(models.Model):
    _name = 'buy.order.line'
    _description = u'采购订单明细'

    @api.one
    @api.depends('goods_id')
    def _compute_uom_id(self):
        '''当订单行的产品变化时，带出产品上的单位'''
        self.uom_id = self.goods_id.uom_id

    @api.model
    def _default_warehouse(self):
        context = self._context or {}
        if context.get('warehouse_type'):
            return self.pool.get('warehouse').get_warehouse_by_type(self._cr, self._uid, context.get('warehouse_type'))

        return False

    @api.model
    def _default_warehouse_dest(self):
        context = self._context or {}
        if context.get('warehouse_dest_type'):
            return self.pool.get('warehouse').get_warehouse_by_type(self._cr, self._uid, context.get('warehouse_dest_type'))

        return False

    @api.one
    @api.depends('quantity', 'price', 'discount_rate', 'tax_rate')
    def _compute_all_amount(self):
        '''当订单行的数量、购货单价、折扣率、税率改变时，改变折扣额、金额、税额、价税合计'''
        amt = self.quantity * self.price
        discount = amt * self.discount_rate * 0.01
        amount = amt - discount
        tax_amt = amount * self.tax_rate * 0.01
        self.price_taxed = self.price * (1 + self.tax_rate * 0.01)
        self.discount = discount
        self.amount = amount
        self.tax_amount = tax_amt
        self.subtotal = amount + tax_amt

    goods_id = fields.Many2one('goods', u'商品')
    spec = fields.Char(u'属性')
    uom_id = fields.Many2one('uom', u'单位', compute=_compute_uom_id, store=True,readonly=True)
    warehouse_id = fields.Many2one('warehouse', u'调出仓库', default=_default_warehouse)
    warehouse_dest_id = fields.Many2one('warehouse', u'调入仓库', default=_default_warehouse_dest)
    quantity = fields.Float(u'数量', default=1)
    price = fields.Float(u'购货单价')
    price_taxed = fields.Float(u'含税单价', compute=_compute_all_amount, store=True,readonly=True)
    discount_rate = fields.Float(u'折扣率%')
    discount = fields.Float(u'折扣额', compute=_compute_all_amount, store=True,readonly=True)
    amount = fields.Float(u'金额', compute=_compute_all_amount, store=True,readonly=True)
    tax_rate = fields.Float(u'税率(%)', default=17.0)
    tax_amount = fields.Float(u'税额', compute=_compute_all_amount, store=True,readonly=True)
    subtotal = fields.Float(u'价税合计', compute=_compute_all_amount, store=True,readonly=True)
    note = fields.Char(u'备注')
    origin = fields.Char(u'源单号')
    order_id = fields.Many2one('buy.order', u'订单编号', select=True, required=True, ondelete='cascade')

class buy_receipt(models.Model):
    _name = "buy.receipt"
    _inherits = {'wh.move': 'buy_move_id'}
    _inherit = ['mail.thread']
    _description = u"采购入库单"

    @api.one
    @api.depends('line_in_ids.subtotal', 'discount_rate', 'payment')
    def _compute_all_amount(self):
        '''当优惠率改变时，改变优惠金额和优惠后金额'''
        self.total = sum(line.subtotal for line in self.line_in_ids)
        self.discount_amount = self.total * self.discount_rate * 0.01
        self.amount = self.total - self.discount_amount
        self.debt = self.amount - self.payment

    buy_move_id = fields.Many2one('wh.move', u'入库单', required=True, ondelete='cascade')
    origin = fields.Char(u'源单号', copy=False)
    date_due = fields.Date(u'到期日期', copy=False)
    discount_rate = fields.Float(u'优惠率(%)', states=READONLY_STATES)
    discount_amount = fields.Float(u'优惠金额', compute=_compute_all_amount, states=READONLY_STATES)
    amount = fields.Float(u'优惠后金额', compute=_compute_all_amount, store=True,readonly=True)
    payment = fields.Float(u'本次付款', states=READONLY_STATES)
    bank_account_id = fields.Many2one('bank.account', u'结算账户', default='(空)')
    debt = fields.Float(u'本次欠款', compute=_compute_all_amount, copy=False, store=True,readonly=True)
    cost_line_ids = fields.One2many('cost.line', 'buy_id', u'采购费用', copy=False)
    state = fields.Selection(BUY_RECEIPT_STATES, u'付款状态', default='draft', readonly=True, help=u"采购入库单的状态", select=True, copy=False)

    @api.model
    def create(self, vals):
        '''创建采购入库单时判断结算账户和付款额'''
        a = self.bank_account_id
        b = (self.payment==0)
        c = vals.get('bank_account_id')
        d = (vals.get('payment')==0)
        if (a or c) and d:
            raise except_orm(u'警告！', u'结算账户不为空时，需要输入付款额！')
        elif not b and not (a or c):
            raise except_orm(u'警告！', u'付款额不为空时，请选择结算账户！')
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get(self._name) or '/'
        return super(buy_receipt, self).create(vals)

    @api.multi
    def write(self, vals):
        '''修改采购入库单时判断结算账户和付款额'''
        a = self.bank_account_id
        b = (self.payment==0)
        c = vals.get('bank_account_id')
        d = (vals.get('payment')==0)
        if (a or c) and d:
            raise except_orm(u'警告！', u'结算账户不为空时，需要输入付款额！')
        elif (not b or not d) and not (a or c):
            raise except_orm(u'警告！', u'付款额不为空时，请选择结算账户！')
        return super(buy_receipt, self).write(vals)

    @api.one
    def buy_in_approve(self):
        '''审核采购入库单，更新购货订单的状态和本单的付款状态，并生成源单'''
        order = self.env['buy.order'].search([('name', '=', self.origin)])
        for line in order.line_ids:
            for line_in in self.line_in_ids:
                if line.goods_id.id == line_in.goods_id.id:
                    if line.quantity > line_in.goods_qty:
                        order.write({'state': 'part_in'})
                    elif line.quantity == line_in.goods_qty:
                        order.write({'state': 'all_in'})

        if self.payment > self.amount:
            raise except_orm(u'警告！', u'本次付款金额不能大于折后金额！')
        elif self.payment == 0:
            self.write({'state': 'confirmed'})
        elif self.payment < self.amount:
            self.write({'state': 'part_paid'})
        else:
            self.write({'state': 'paid'})
        self.write({'approve_uid': self._uid})

        # 入库单生成源单
        categ = self.env['core.category'].search([('type', '=', 'expense')])
        source_id = self.env['money.invoice'].create({
                            'name': self.name,
                            'partner_id': self.partner_id.id,
                            'category_id': categ.id,
                            'date': fields.Date.context_today(self),
                            'amount': self.amount,
                            'reconciled': self.payment,
                            'to_reconcile': self.debt,
                            'date_due': self.date_due,
                            'state': 'done',
                        })
        # 采购费用产生源单
        if sum(cost_line.amount for cost_line in self.cost_line_ids) > 0:
            categ = self.env['core.category'].search([('type', '=', 'attribute')])
            for line in self.cost_line_ids:
                self.env['money.invoice'].create({
                            'name': self.name,
                            'partner_id': self.partner_id.id,
                            'category_id': categ.id,
                            'date': fields.Date.context_today(self),
                            'amount': line.amount,
                            'reconciled': 0.0,
                            'to_reconcile': line.amount,
                            'date_due': self.date_due,
                            'state': 'done',
                        })
        # 生成付款单
        money_lines = []
        source_lines = []
        money_lines.append({
            'bank_id': self.bank_account_id.id,
            'amount': self.payment,
        })
        source_lines.append({
            'name': source_id.id,
            'category_id': categ.id,
            'date': source_id.date,
            'amount': self.amount,
            'reconciled': 0.0,
            'to_reconcile': self.amount,
            'this_reconcile': self.payment,
        })

        self.env['money.order'].create({
                            'partner_id': self.partner_id.id,
                            'date': fields.Date.context_today(self),
                            'line_ids': [(0, 0, line) for line in money_lines],
                            'source_ids': [(0, 0, line) for line in source_lines],
                            'type': 'pay',
                            'amount': self.amount,
                            'reconciled': self.payment,
                            'to_reconcile': self.debt,
                            'state': 'done',
                        })
        return True

    @api.one
    def buy_in_refuse(self):
        '''反审核采购入库单'''
        self.write({'state': 'draft'})
        return True

    @api.one
    def buy_share_cost(self):
        '''入库单上的采购费用分摊到入库单明细行上'''
        total_amount = 0
        for line in self.line_in_ids:
            total_amount += line.amount
        print '合计采购金额：',total_amount
        for line in self.line_in_ids:
            line.share_cost = sum(cost_line.amount for cost_line in self.cost_line_ids) / total_amount * line.amount
        return True

class buy_receipt_line(models.Model):
    _inherit = 'wh.move.line'
    _description = u"采购入库明细"

    @api.one
    @api.depends('goods_qty', 'price', 'discount_rate', 'tax_rate')
    def _compute_all_amount(self):
        '''当订单行的数量、购货单价、折扣率、税率改变时，改变折扣额、金额、税额、价税合计'''
        amt = self.goods_qty * self.price
        discount = amt * self.discount_rate * 0.01
        amount = amt - discount
        tax_amt = amount * self.tax_rate * 0.01
        self.price_taxed = self.price * (1 + self.tax_rate * 0.01)
        self.discount = discount
        self.amount = amount
        self.tax_amount = tax_amt
        self.subtotal = amount + tax_amt

    spec = fields.Char(u'属性')
    price_taxed = fields.Float(u'含税单价', compute=_compute_all_amount, store=True,readonly=True)
    discount_rate = fields.Float(u'折扣率%')
    discount = fields.Float(u'折扣额', compute=_compute_all_amount, store=True,readonly=True)
    amount = fields.Float(u'购货金额', compute=_compute_all_amount, store=True,readonly=True)
    tax_rate = fields.Float(u'税率(%)', default=17.0)
    tax_amount = fields.Float(u'税额', compute=_compute_all_amount, store=True,readonly=True)
    subtotal = fields.Float(u'价税合计', compute=_compute_all_amount, store=True,readonly=True)
    share_cost = fields.Float(u'采购费用')

class cost_line(models.Model):
    _name = 'cost.line'
    _description = u"采购销售费用"

    buy_id = fields.Many2one('buy.receipt', u'入库单号')
    sell_id = fields.Many2one('sell.delivery', u'出库单号')
    partner_id = fields.Many2one('partner', u'供应商')
    category_id = fields.Many2one('core.category', string=u'类别')
    amount = fields.Float(u'金额')
    note = fields.Char(u'备注')