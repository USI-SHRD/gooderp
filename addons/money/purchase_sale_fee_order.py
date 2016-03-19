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

from openerp.exceptions import except_orm
from openerp import fields, models, api

class fee_order(models.Model):
    _name = 'fee.order'
    _description = u"采购销售费用清单"

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values.update({'name': self.env['ir.sequence'].get('fee_order') or '/'})

        return super(fee_order, self).create(values)

    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    date = fields.Date(string=u'日期', default=lambda self: fields.Date.context_today(self))
    name = fields.Char(string=u'单据编号', copy=False, readonly=True, default='/')
    pay_type = fields.Char(string=u'支出类别')
    amount = fields.Float(string=u'金额')
    unpaid_amount = fields.Float(string=u'未付金额')
    source_id = fields.Char(string=u'源单')
    other_payment_list = fields.Char(string=u'其他支出单编号')
    source_date = fields.Date(string=u'源单日期')
    is_pay_apply = fields.Boolean(string=u'是否已申请付款')

class fee_order_wizard(models.Model):
    _name = 'fee.order.wizard'
    _description = u"费用清单支付向导"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(fee_order_wizard, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        active_ids = self._context.get('active_ids')
        fee_order = self.env['fee.order'].search([('id', 'in', active_ids)])
        supplier = set([fee.partner_id.id for fee in fee_order])
        if len(supplier) > 1:
            raise except_orm(u'错误', u'只能为相同供应商支付费用')
        for fee in fee_order:
            if fee.is_pay_apply:
                raise except_orm(u'警告', u'%s已申请过付款' % fee.name)
        return res

    @api.multi
    def pay_fee(self):
        # 支付费用
        active_ids = self._context.get('active_ids')
        fee_order = self.env['fee.order'].search([('id', 'in', active_ids)])
        supplier = set([fee.partner_id.id for fee in fee_order])

        lines = []
        for fee in fee_order:
            lines.append((0, 0, {
                    'other_money_type': fee.pay_type,
                    'amount': fee.unpaid_amount,
                    'other_money_source': fee.id,
                    'note': '',
                }))
        pay_id = self.env['other.money.order'].create({
                            'partner_id': list(supplier)[0],
                            'line_ids': lines,
                            'type': 'other_pay',
                        })

        res = self.env['ir.model.data'].get_object_reference('money', 'other_money_order_form')
        view_id = res and res[1] or False

        fee_order.write({'is_pay_apply': True})
        return {
            'name': u'其他付款单',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(view_id, 'form')],
            'res_model': 'other.money.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': pay_id and pay_id.id or False,
        }
