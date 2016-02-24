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
# from warehouse import wh_move, wh_move_line

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

    _columns = {
        'partner_id': fields.many2one('partner', u'供应商', required=True, states=READONLY_STATES),
        'date': fields.date(u'单据日期', states=READONLY_STATES,
                select=True, help=u"描述了询价单转换成采购订单的日期，默认是订单创建日期。", copy=False),
        'planned_date':fields.date(u'交货日期', states=READONLY_STATES, select=True, help=u"订单的预计交货日期"),
        'name': fields.char(u'单据编号', required=True, select=True, copy=False,
                help=u"采购订单的唯一编号，当创建时它会自动生成有序编号。"),
        'type': fields.selection([('buy','购货'),('return','退货')], u'类型'),
        'line_ids': fields.one2many('buy.order.line', 'order_id', u'采购订单行', states=READONLY_STATES, copy=True),
        'notes': fields.text(u'备注', states=READONLY_STATES),
        'discount_rate': fields.float(u'优惠率(%)', states=READONLY_STATES),
        'discount_amount': fields.float(u'优惠金额', states=READONLY_STATES),
        'amount': fields.float(u'优惠后金额', states=READONLY_STATES,),
        'validator_id': fields.many2one('res.users', u'审核人', copy=False),
        'state': fields.selection(BUY_ORDER_STATES, u'状态', readonly=True, help=u"采购订单的状态", select=True, copy=False),     
    }
    _defaults = {
        'date': fields.date.context_today,
        'planned_date': fields.date.context_today,
        'name': lambda self, cr, uid, context: \
                        self.pool.get('ir.sequence').get(cr, uid, 'buy.order', context=context),
        'type': 'buy',
        'state': 'draft',
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name)', '采购订单号必须唯一!'),
    ]

    def create(self, cr, uid, vals, context=None):
        context = dict(context or {}, mail_create_nolog=True)
        order =  super(buy_order, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [order], body=u'购货订单已创建', context=context)
        return order

    def onchange_discount_rate(self, cr, uid, ids, discount_rate, context=None):
        '''当优惠率改变时，改变优惠金额和优惠后金额'''
        total = 0
        for line in self.browse(cr, uid, ids, context=context).line_ids:
            total += line.subtotal
        discount_amount = total * discount_rate * 0.01
        return {'value':{
                         'discount_amount': discount_amount,
                         'amount': total - discount_amount,
                         }
                }

    def buy_approve(self, cr, uid, ids, context=None):
        '''审核购货订单'''
        assert(len(ids) == 1), 'This option should only be used for a single id at a time'
        self.write(cr, uid, ids, {'state': 'approved', 'validator_id': uid})
        return True

    def buy_refuse(self, cr, uid, ids, context=None):
        '''反审核购货订单'''
        assert(len(ids) == 1), 'This option should only be used for a single id at a time'
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def buy_generate_order(self, cr, uid, ids, context=None):
        '''由购货订单生成购货单'''
        assert(len(ids) == 1), 'This option should only be used for a single id at a time'
        self.write(cr, uid, ids, {'state': 'confirmed'})
        return True

class buy_order_line(osv.osv):
    _name = 'buy.order.line'
    _description = u'采购订单明细'
    _columns = {
        'goods_id': fields.many2one('goods', u'商品'),
        'spec': fields.char(u'属性'),
        'uom_id': fields.many2one('uom', u'单位'),
        'warehouse_id': fields.many2one('warehouse', u'仓库'),
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

    _columns = {
        'buy_move_id': fields.many2one('wh.move', u'入库单'),
        'discount_rate': fields.float(u'优惠率(%)', states=READONLY_STATES),
        'discount_amount': fields.float(u'优惠金额', states=READONLY_STATES),
        'amount': fields.float(u'优惠后金额', states=READONLY_STATES),
        'payment': fields.float(u'本次付款', states=READONLY_STATES),
        'bank_account_id': fields.many2one('bank.account', u'结算账户'),
        'debt': fields.float(u'本次欠款'),
        'total_cost': fields.float(u'采购费用'),
        'state': fields.selection(BUY_ORDER_STATES, u'状态', readonly=True, help=u"采购入库单的状态", select=True, copy=False),
    }
    _defaults ={
        'date': fields.date.context_today,
        'name': lambda self, cr, uid, context: \
                        self.pool.get('ir.sequence').get(cr, uid, 'buy.order', context=context),
        'bank_account_id': '(空)',
    }

    def create(self, cr, uid, vals, context=None):
        context = dict(context or {}, mail_create_nolog=True)
        receipt =  super(buy_receipt, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [receipt], body=u'采购入库单已创建', context=context)
        return receipt

    def onchange_discount_rate(self, cr, uid, ids, discount_rate, context=None):
        '''当优惠率改变时，改变优惠金额和优惠后金额'''
        total = 0
        for line in self.browse(cr, uid, ids, context=context).line_in_ids:
            total += line.subtotal
        discount_amount = total * discount_rate * 0.01
        return {'value':{
                         'discount_amount': discount_amount,
                         'amount': total - discount_amount,
                         }
                }

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