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

from openerp.osv import fields, osv
from openerp import models, api, _
from openerp import fields as Fields

BUY_ORDER_STATES = [
        ('draft', '草稿'),
        ('approved', '已审核'),
        ('confirmed', '购货单'),
    ]
READONLY_STATES = {
        'approved': [('readonly', True)],
        'confirmed': [('readonly', True)],
    }
class buy_order(osv.osv):
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

#     @api.model
#     def _default_name(self):
#         return self.env['ir.sequence'].get('buy.order')

    partner_id = Fields.Many2one('partner', u'供应商', required=True, states=READONLY_STATES)
    date = Fields.Date(u'单据日期', states=READONLY_STATES, default=lambda self: Fields.Date.context_today(self),
            select=True, help=u"描述了询价单转换成采购订单的日期，默认是订单创建日期。", copy=False)
    planned_date = Fields.Date(u'交货日期', states=READONLY_STATES, default=lambda self: Fields.Date.context_today(self), select=True, help=u"订单的预计交货日期")
    name = Fields.Char(u'单据编号', required=True, select=True, copy=False,
        default=lambda self: self.env['ir.sequence'].get('buy.order'), help=u"采购订单的唯一编号，当创建时它会自动生成有序编号。")
    type = Fields.Selection([('buy','购货'),('return','退货')], u'类型', default='buy')
    line_ids = Fields.One2many('buy.order.line', 'order_id', u'采购订单行', states=READONLY_STATES, copy=True)
    notes = Fields.Text(u'备注', states=READONLY_STATES)
    discount_rate = Fields.Float(u'优惠率(%)', states=READONLY_STATES)
    validator_id = Fields.Many2one('res.users', u'审核人', copy=False)
    state = Fields.Selection(BUY_ORDER_STATES, u'状态', readonly=True, help=u"采购订单的状态", select=True, copy=False, default='draft')
    total = Fields.Float(string=u'合计', store=True,
            compute='_compute_amount', track_visibility='always', help=u'所有订单行小计之和')
    discount_amount = Fields.Float(string=u'优惠金额', store=True, states=READONLY_STATES,
            compute='_compute_amount', track_visibility='always')
    amount = Fields.Float(string=u'优惠后金额', store=True, states=READONLY_STATES,
            compute='_compute_amount', track_visibility='always')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', '采购订单号必须唯一!'),
    ]

    @api.multi
    def buy_approve(self):
        '''审核购货订单'''
        assert(len(self._ids) == 1), 'This option should only be used for a single id at a time'
        self.write({'state': 'approved', 'validator_id': self._uid})
        return True

    @api.multi
    def buy_refuse(self):
        '''反审核购货订单'''
        assert(len(self._ids) == 1), 'This option should only be used for a single id at a time'
        self.write({'state': 'draft'})
        return True

    @api.multi
    def buy_generate_order(self):
        '''由购货订单生成采购入库单'''
        assert(len(self._ids) == 1), 'This option should only be used for a single id at a time'

        res = []
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
                'discount': line.discount,
                'amount': line.amount,
                'tax_rate': line.tax_rate,
                'tax_amount': line.tax_amount,
                'subtotal': line.subtotal or 0.0,
                'note': line.note or '',
                'share_cost': 0,
            })
            print 'dict:',dict

        for i in range(len(dict)):
            ret.append((0, 0, dict[i]))
        print 'ret:',ret
        receipt_id = self.pool.get('buy.receipt').create(self._cr, self._uid, {
                            'partner_id': self.partner_id.id,
                            'line_in_ids': ret,
                            'discount_rate': self.discount_rate,
                            'discount_amount': self.discount_amount,
                            'amount': self.amount,
#                             'debt':,
#                             'total_cost':,
                            'state': 'draft',
                        }, context=self._context)
        print 'partner_id', self.partner_id.id
        res.append(receipt_id)
        view_id = self.env['ir.model.data'].xmlid_to_res_id('gooderp.buy_receipt_form')
        self.write({'state': 'confirmed'})
        return {
            'name': u'采购入库单',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(view_id, 'form')],
            'res_model': 'buy.receipt',
            'type': 'ir.actions.act_window',
            'domain':[('id','in',res)],
#             'target': 'self',
        }

class buy_order_line(osv.osv):
    _name = 'buy.order.line'
    _description = u'采购订单明细'

    def _get_default_warehouse(self, cr, uid, context=None):
        context = context or {}
        if context.get('warehouse_type'):
            return self.pool.get('warehouse').get_warehouse_by_type(cr, uid, context.get('warehouse_type'))

        return False
    _columns = {
        'goods_id': fields.many2one('goods', u'商品'),
        'spec': fields.char(u'属性'),
        'uom_id': fields.many2one('uom', u'单位'),
        'warehouse_id': fields.many2one('warehouse', u'调出仓库'),
        'warehouse_dest_id': fields.many2one('warehouse', u'调入仓库'),
        'quantity': fields.float(u'数量'),
        'price': fields.float(u'购货单价'),
        'discount_rate': fields.float(u'折扣率%'),
        'discount': fields.float(u'折扣额'),
        'amount': fields.float(u'金额'),
        'tax_rate': fields.float(u'税率(%)'),
        'tax_amount': fields.float(u'税额'),
        'subtotal': fields.float(u'价税合计'),
        'note': fields.char(u'备注'),
        'origin': fields.char(u'源单号'),
        'order_id': fields.many2one('buy.order', u'订单编号', select=True, required=True, ondelete='cascade'),
    }

    _defaults = {
        'warehouse_id': _get_default_warehouse,
#         'warehouse_dest_id': _get_default_warehouse_dest,
    }
    def onchange_goods_id(self, cr, uid, ids, goods_id, context=None):
        '''当订单行的产品变化时，带出产品上的单位'''
        return {'value':{
                         'uom_id': self.pool.get('goods').browse(cr, uid, goods_id, context=context).uom_id,
                         }
                }

    def onchange_price(self, cr, uid, ids, price, quantity, discount_rate, tax_rate, context=None):
        '''当订单行的数量、购货单价、折扣率、税率改变时，改变折扣额、金额、税额、价税合计'''
        amt = price * quantity
        discount = amt * discount_rate * 0.01
        amount = amt - discount
        tax_amt = amount * tax_rate * 0.01
        return {'value':{
                         'discount': discount,
                         'amount': amount,
                         'tax_amount': tax_amt,
                         'subtotal': amount + tax_amt,
                         }
                }

class buy_receipt(osv.osv):
    _name = "buy.receipt"
    _inherits = {'wh.move': 'buy_move_id'}
    _inherit = ['mail.thread']
    _description = u"采购入库单"

    @api.one
    @api.depends('line_in_ids.subtotal', 'discount_rate')
    def _compute_amount(self):
        '''当优惠率改变时，改变优惠金额和优惠后金额'''
        self.total = sum(line.subtotal for line in self.line_in_ids)
        self.discount_amount = self.total * self.discount_rate * 0.01
        self.amount = self.total - self.discount_amount

    buy_move_id = Fields.Many2one('wh.move', u'入库单', required=True, index=True, ondelete='cascade')
    discount_rate = Fields.Float(u'优惠率(%)', states=READONLY_STATES)
    discount_amount = Fields.Float(u'优惠金额', states=READONLY_STATES)
    amount = Fields.Float(u'优惠后金额', states=READONLY_STATES)
    payment = Fields.Float(u'本次付款', states=READONLY_STATES)
    bank_account_id = Fields.Many2one('bank.account', u'结算账户', default='(空)')
    debt = Fields.Float(u'本次欠款')
    total_cost = Fields.Float(u'采购费用')
    state = Fields.Selection(BUY_ORDER_STATES, u'状态', readonly=True, help=u"采购入库单的状态", select=True, copy=False)

class buy_receipt_line(osv.osv):
    _inherit = 'wh.move.line'
    _description = u"采购入库明细"
    _columns = {
        'spec': fields.char(u'属性'),
        'discount_rate': fields.float(u'折扣率%'),
        'discount': fields.float(u'折扣额'),
        'amount': fields.float(u'购货金额'),
        'tax_rate': fields.float(u'税率(%)'),
        'tax_amount': fields.float(u'税额'),
        'subtotal': fields.float(u'价税合计'),
        'share_cost': fields.float(u'采购费用'),
    }

    def onchange_price(self, cr, uid, ids, price, quantity, discount_rate, tax_rate, context=None):
        '''当订单行的数量、购货单价、折扣率、税率改变时，改变折扣额、金额、税额、价税合计'''
        amt = price * quantity
        discount = amt * discount_rate * 0.01
        amount = amt - discount
        tax_amt = amount * tax_rate * 0.01
        return {'value':{
                         'discount': discount,
                         'amount': amount,
                         'tax_amount': tax_amt,
                         'subtotal': amount + tax_amt,
                         }
                }