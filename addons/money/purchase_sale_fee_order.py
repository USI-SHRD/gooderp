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

class purchase_sale_fee_order(osv.osv):
    _name = 'purchase.sale.fee.order'
    _description = u"采购销售费用清单"
    
    TYPE_PAY_SELECTION = [
        ('unpaid', u'未付款'),
        ('paid', u'已付款'),
        ('partial_paid', u'部分付款'),
    ]

    _columns = {
        'state': fields.selection([
                  ('draft', u'未付款'),
                  ('done', u'已付款'),
                  ('cancel', u'已取消')
                   ], u'状态', readonly=True, copy=False),
        'partner_id': fields.many2one('partner', u'供应商', required=True),
        'from_date': fields.date(u'开始日期'),
        'end_date': fields.date(u'结束日期'),
        'name': fields.char(u'单据编号', copy=False, readonly=True),
        'type': fields.selection(TYPE_PAY_SELECTION, u'付款状态'),
    }

    _defaults = {
        'state': 'draft',
        'date': fields.date.context_today,
  }

class purchase_sale_fee_order_line(osv.osv):
    _name = 'purchase.sale.fee.order.line'
    _description = u'采购销售费用清单明细'

    _columns = {
                'state': fields.selection([
                          ('draft', u'未付款'),
                          ('done', u'已付款'),
                          ('cancel', u'已取消')
                           ], u'状态', readonly=True, copy=False),
                'partner_id': fields.many2one('partner', u'供应商', required=True),
                'pay_type': fields.char(u'支出类别'),
                'amount': fields.float(u'金额'),
                'unpaid_amount': fields.float(u'未付费用'),
                'source_id': fields.char(u'源单'),
                'other_payment_list': fields.char(u'其他支出单编号'), #
                'source_date': fields.date(u'源单编号'),
                }