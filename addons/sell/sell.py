# -*- encoding: utf-8 -*-

from openerp import fields, models, api
from openerp.exceptions import except_orm

SELL_ORDER_STATES = [
        ('draft', u'草稿'),
        ('approved', u'已审核'),
        ('confirmed', u'未出库'),
        ('part_out', u'部分出库'),
        ('all_out', u'全部出库'),
    ]
SELL_DELIVERY_STATES = [
        ('draft', u'草稿'),
        ('approved', u'已审核'),
        ('confirmed', u'未收款'),
        ('part_receipted', u'部分收款'),
        ('receipted', u'全部收款'),
    ]
READONLY_STATES = {
        'approved': [('readonly', True)],
        'confirmed': [('readonly', True)],
    }

class sell_order(models.Model):
    _name = 'sell.order'
    _description = "Sell Order"
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    @api.one
    @api.depends('line_ids.subtotal', 'benefit_rate')
    def _compute_amount(self):
        '''计算订单合计金额，并且当优惠率改变时，改变优惠金额和优惠后金额'''
        self.total = sum(line.subtotal for line in self.line_ids)
        self.benefit_amount = self.total * self.benefit_rate * 0.01
        self.amount = self.total - self.benefit_amount

    partner_id = fields.Many2one('partner', u'客户', states=READONLY_STATES)
    staff_id = fields.Many2one('staff',u'销售员',states=READONLY_STATES)
    date = fields.Date(u'单据日期', states=READONLY_STATES, default=lambda self: fields.Date.context_today(self),
            select=True, help=u"默认是订单创建日期", copy=False)
    delivery_date = fields.Date(u'交货日期', states=READONLY_STATES, default=lambda self: fields.Date.context_today(self), select=True, help=u"订单的预计交货日期")
    type = fields.Selection([('sell',u'销货'),('return', u'退货')], u'类型', default='sell')
    name = fields.Char(u'单据编号', select=True, copy=False,
        default='/', help=u"创建时它会自动生成有序编号")
    line_ids = fields.One2many('sell.order.line', 'order_id', u'销售订单行', states=READONLY_STATES, copy=True)
    note = fields.Text(u'备注', states=READONLY_STATES)
    benefit_rate = fields.Float(u'优惠率(%)', states=READONLY_STATES)
    benefit_amount = fields.Float(string=u'优惠金额', store=True, states=READONLY_STATES,
            compute='_compute_amount', track_visibility='always')
    amount = fields.Float(string=u'优惠后金额', store=True, states=READONLY_STATES,
            compute='_compute_amount', track_visibility='always')
    approve_uid = fields.Many2one('res.users', u'审核人', copy=False)
    state = fields.Selection(SELL_ORDER_STATES, u'订单状态', readonly=True, help=u"销售订单的状态", select=True, copy=False, default='draft')

    _sql_constraints = [
        ('name_uniq','unique(name)','销售订单号必须唯一！'),
    ]

    @api.model
    def create(self, vals):
        if not vals.get('line_ids'):
            raise except_orm(u'警告！', u'请输入产品明细行！')
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get(self._name) or '/'
        return super(sell_order, self).create(vals)

    @api.one
    def sell_approve(self):
        '''审核销货订单'''
        self.write({'state': 'approved', 'approve_uid': self._uid})
        return True

    @api.one
    def sell_refuse(self):
        '''反审核销货订单'''
        if self.state == 'confirmed':
            raise except_orm(u'警告！', u'该单据已经生成了关联单据，不能反审核！')
        self.write({'state': 'draft', 'approve_uid': ''})
        return True

    @api.one
    def sell_generate_delivery(self):
        '''由销货订单生成销售发货单'''
        dict = []
        ret = []

        for line in self.line_ids:
            dict.append({
                'goods_id': line.goods_id and line.goods_id.id or '',
                'spec': line.spec,
                'uom_id': line.uom_id.id,
                'warehouse_id': line.warehouse_id and line.warehouse_id.id or '',
                'warehouse_dest_id': line.warehouse_dest_id and line.warehouse_dest_id.id or '',
                'goods_qty': line.quantity,
                'price': line.price,
                'discount_rate': line.discount_rate,
                'discount_amount': line.discount_amount,
                'amount': line.amount,
                'tax_rate': line.tax_rate,
                'tax_amount': line.tax_amount,
                'subtotal': line.subtotal or 0.0,
                'note': line.line_note or '',
            })

        for i in range(len(dict)):
            ret.append((0, 0, dict[i]))
        delivery_id = self.env['sell.delivery'].create({
                            'partner_id': self.partner_id.id,
                            'staff_id': self.staff_id.id,
                            'date': fields.Date.context_today(self),
                            'origin': self.name,
                            'line_out_ids': ret,
                            'note': self.note,
                            'benefit_rate': self.benefit_rate,
                            'benefit_amount': self.benefit_amount,
                            'amount': self.amount,
                            'state': 'draft',
                        })
        view_id = self.env['ir.model.data'].xmlid_to_res_id('sell.sell_delivery_form')
        self.write({'state': 'confirmed'})
        return {
            'name': u'销售发货单',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(view_id, 'form')],
            'res_model': 'sell.delivery',
            'type': 'ir.actions.act_window',
            'domain':[('id', '=', delivery_id)],
            'target': 'current',
        }

class sell_order_line(models.Model):
    _name = 'sell.order.line'
    _description = u'销货订单明细'

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
        discount_amount = amt * self.discount_rate * 0.01
        amount = amt - discount_amount
        tax_amt = amount * self.tax_rate * 0.01
        self.price_taxed = self.price * (1 + self.tax_rate * 0.01)
        self.discount_amount = discount_amount
        self.amount = amount
        self.tax_amount = tax_amt
        self.subtotal = amount + tax_amt

    order_id = fields.Many2one('sell.order', u'订单编号', select=True, required=True, ondelete='cascade')
    goods_id = fields.Many2one('goods', u'商品')
    spec = fields.Char(u'属性') #产品的属性，选择产品时自动从产品管理表获取
    uom_id = fields.Many2one('uom', u'单位', compute=_compute_uom_id)
    warehouse_id = fields.Many2one('warehouse', u'调出仓库', default=_default_warehouse)
    warehouse_dest_id = fields.Many2one('warehouse', u'调入仓库', default=_default_warehouse_dest)
    quantity = fields.Float(u'数量', default=1)
    price = fields.Float(u'销售单价')
    price_taxed = fields.Float(u'含税单价', compute=_compute_all_amount)
    discount_rate = fields.Float(u'折扣率%')
    discount_amount = fields.Float(u'折扣额', compute=_compute_all_amount)
    amount = fields.Float(u'金额', compute=_compute_all_amount)
    tax_rate = fields.Float(u'税率(%)', default=17.0)
    tax_amount = fields.Float(u'税额', compute=_compute_all_amount)
    subtotal = fields.Float(u'价税合计', compute=_compute_all_amount)
    line_note = fields.Char(u'备注')

class sell_delivery(models.Model):
    _name = 'sell.delivery'
    _inherits = {'wh.move': 'sell_move_id'}
    _description = u'销售发货单'
    _order = 'date desc, id desc'

    @api.one
    @api.depends('line_out_ids.subtotal', 'benefit_rate', 'receipt', 'partner_id')
    def _compute_all_amount(self):
        '''当优惠率改变时，改变优惠金额和优惠后金额'''
        self.total = sum(line.subtotal for line in self.line_out_ids)
        self.benefit_amount = self.total * self.benefit_rate * 0.01
        self.amount = self.total - self.benefit_amount
        self.debt = self.amount - self.receipt
        self.total_debt = self.partner_id.receivable

    sell_move_id = fields.Many2one('wh.move', u'出库单', required=True, ondelete='cascade')
    staff_id = fields.Many2one('res.users', u'销售员')
    origin = fields.Char(u'源单号', copy=False)
    date_due = fields.Date(u'到期日期', copy=False)
    benefit_rate = fields.Float(u'优惠率(%)', states=READONLY_STATES)
    benefit_amount = fields.Float(u'优惠金额', compute=_compute_all_amount, states=READONLY_STATES)
    amount = fields.Float(u'优惠后金额', compute=_compute_all_amount, states=READONLY_STATES)
    partner_cost = fields.Float(u'客户承担费用')
    receipt = fields.Float(u'本次收款', states=READONLY_STATES)
    bank_account_id = fields.Many2one('bank.account', u'结算账户', default=u'(空)')
    debt = fields.Float(u'本次欠款', compute=_compute_all_amount, copy=False)
    total_debt = fields.Float(u'总欠款', compute=_compute_all_amount, copy=False)
    total_cost = fields.Float(u'销售费用', copy=False)
    state = fields.Selection(SELL_DELIVERY_STATES, u'收款状态', default='draft', readonly=True, help=u"销售发货单的状态", select=True, copy=False)

    @api.model
    def create(self, vals):
        '''创建时判断结算账户和收款额'''
        a = self.bank_account_id
        b = (self.receipt==0)
        c = vals.get('bank_account_id')
        d = (vals.get('receipt')==0)
        if (a or c) and d:
            raise except_orm(u'警告！', u'结算账户不为空时，需要输入收款额！')
        elif not b and not (a or c):
            raise except_orm(u'警告！', u'收款额不为空时，请选择结算账户！')
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get(self._name) or '/'
        return super(sell_delivery, self).create(vals)

    @api.multi
    def write(self, vals):
        '''修改销售发货单时判断结算账户和收款额'''
        a = self.bank_account_id
        b = (self.receipt==0)
        c = vals.get('bank_account_id')
        d = (vals.get('receipt')==0)
        if (a or c) and d:
            raise except_orm(u'警告！', u'结算账户不为空时，需要输入收款额！')
        elif not b and not (a or c):
            raise except_orm(u'警告！', u'收款额不为空时，请选择结算账户！')
        return super(sell_delivery, self).write(vals)

    @api.one
    def sell_out_approve(self):
        '''审核销售发货单，更新销货订单的状态和本单的收款状态，并生成源单'''
        order = self.env['sell.order'].search([('name', '=', self.origin)])
        for line in order.line_ids:
            if line.goods_id.id == self.line_out_ids.goods_id.id:
                if line.quantity > self.line_out_ids.goods_qty:
                    order.write({'state': 'part_out'})
                elif line.quantity == self.line_out_ids.goods_qty:
                    order.write({'state': 'all_out'})

        if self.receipt > self.amount:
            raise except_orm(u'警告！', u'本次收款金额不能大于优惠后金额！')
        elif self.receipt == 0:
            self.write({'state': 'confirmed'})
        elif self.receipt < self.amount:
            self.write({'state': 'part_receipted'})
        else:
            self.write({'state': 'receipted'})

        # 审核之后更新客户的应收余额
        partner = self.env['partner'].search([('name', '=', self.partner_id.name)])
        partner.write({'receivable': self.debt + self.total_debt})
        self.write({'approve_uid': self._uid})

        # 生成源单
        self.env['money.invoice'].create({
                            'name': self.name,
                            'partner_id': self.partner_id.id,
                            'business_type': u'普通销售',
                            'date': fields.Date.context_today(self),
                            'amount': self.debt,
                            'reconciled': 0.0,
                            'to_reconcile': self.debt,
                            'date_due': self.date_due,
                            'state': 'done',
                        })
        return True

    @api.one
    def sell_out_refuse(self):
        '''反审核销售发货单'''
        self.write({'state': 'draft'})
        return True

class sell_delivery_line(models.Model):
    _inherit = 'wh.move.line'
    _description = u'销售发货单行'

    @api.one
    @api.depends('goods_qty', 'price', 'discount_rate', 'tax_rate')
    def _compute_all_amount(self):
        '''当订单行的数量、购货单价、折扣率、税率改变时，改变折扣额、金额、税额、价税合计'''
        amt = self.goods_qty * self.price
        discount_amount = amt * self.discount_rate * 0.01
        amount = amt - discount_amount
        tax_amt = amount * self.tax_rate * 0.01
        self.price_taxed = self.price * (1 + self.tax_rate * 0.01)
        self.discount_amount = discount_amount
        self.amount = amount
        self.tax_amount = tax_amt
        self.subtotal = amount + tax_amt

    spec = fields.Char(u'属性')
    price_taxed = fields.Float(u'含税单价', compute=_compute_all_amount)
    discount_rate = fields.Float(u'折扣率%')
    discount_amount = fields.Float(u'折扣额', compute=_compute_all_amount)
    amount = fields.Float(u'销售金额', compute=_compute_all_amount)
    tax_rate = fields.Float(u'税率(%)', default=17.0)
    tax_amount = fields.Float(u'税额', compute=_compute_all_amount)
    subtotal = fields.Float(u'价税合计', compute=_compute_all_amount)
    origin = fields.Char(u'源单号')
