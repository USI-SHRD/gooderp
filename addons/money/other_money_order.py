# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016  开阖软件(<http://osbzr.com>).
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

from datetime import datetime
from openerp.osv import fields, osv

class other_money_type(osv.osv):
    _name = 'other.money.type'
    _description = u'支出类别/收入类别'

    _columns = {
        'type':fields.char(u'类型',size=128,required=True),
        'name':fields.char(u'描述',size=128,required=True),
    }
    _defaults = {
        'type':lambda self, cr, uid, ctx:ctx.get('type'),
    }

class other_money_order(osv.osv):
    _name = 'other.money.order'
    _description = u'其他应收款/应付款'
        
    TYPE_SELECTION = [
        ('other_payables', u'其他应付款'),
        ('other_receipts', u'其他应收款'),
    ]

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') and context.get('default_other_receipt'):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'other_receipt_order', context=context) or ''
        if not vals.get('name') and context.get('default_other_payment'):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'other_payment_order', context=context) or ''

        if context.get('default_other_payment'):
            vals.update({'type': 'other_payables'})
        if context.get('default_other_receipt'):
            vals.update({'type': 'other_receipts'})

        return super(other_money_order, self).create(cr, uid, vals, context=context)

    _columns = {
                'state': fields.selection([
                          ('draft', u'草稿'),
                          ('done', u'完成'),
                          ('cancel', u'已取消')
                           ], u'状态', readonly=True, copy=False),
                'partner_id': fields.many2one('partner', u'业务伙伴', required=True),
                'name': fields.char(u'单据编号', copy=False), 
                'date': fields.date(u'单据日期'),
                'total_amount': fields.float(u'应付金额/应收金额'),
                'bank_id': fields.many2one('bank.account',u'结算账户'), #
                'line_ids': fields.one2many('other.money.order.line', 'other_money_id', u'收支单行'),
                'type': fields.selection(TYPE_SELECTION, u'其他应收款/应付款'),
                }

    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
    }

    def print_other_money_order(self, cr, uid, ids, context=None):
        '''打印 其他收入/支出单'''
        assert len(ids) == 1, '一次执行只能有一个id'
        return self.pool['report'].get_action(cr, uid, ids, 'money.report_other_money_order', context=context)

class other_money_order_line(osv.osv):
    _name = 'other.money.order.line'
    _description = u'其他应收应付明细'

    _columns = {
                'other_money_id': fields.many2one('other.money.order', u'其他收入/支出'),
                'other_money_type': fields.many2one('other.money.type', u'支出类别/收入类别'),
                'amount': fields.float(u'金额'),
                'note': fields.char(u'备注'),
                }