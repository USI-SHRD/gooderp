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

from openerp import fields, models, api

class purchase_sale_fee_order(models.Model):
    _name = 'purchase.sale.fee.order'
    _description = u"采购销售费用清单"
    
    TYPE_PAY_SELECTION = [
        ('unpaid', u'未付款'),
        ('paid', u'已付款'),
        ('partial_paid', u'部分付款'),
    ]

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values.update({'name': self.pool['ir.sequence'].get(self._cr, self._uid, 'purchase_sale_fee_order', context=self._context) or '/'})

        return super(purchase_sale_fee_order, self).create(values)

    @api.multi
    def pay_expense(self):
        # 支付费用
        assert(len(self._ids) == 1)
        dict, ret = [], []

        for line in self.line_ids:
            dict.append({
                'other_money_type': line.pay_type,
                'amount': line.amount,
                'note': '',
            })

        for i in range(len(dict)):
            ret.append((0, 0, dict[i]))
        bank_id = self.env['bank.account'].search([('name','=','银行')])
        receipt_id = self.env['other.money.order'].create({
                            'state': 'draft',
                            'partner_id': self.partner_id.id,
                            'date': self.date,
                            'name': '/',
                            'total_amount': sum(line.amount for line in self.line_ids),
                            'bank_id': bank_id.id or False,
                            'line_ids': ret,
                            'type': 'other_payables',
                        })
        self.write({'state': 'done'})
        res = self.env['ir.model.data'].get_object_reference('money', 'other_money_order_form')
        view_id = res and res[1] or False
        return {
            'name': u'选择源单',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(view_id, 'form')],
            'res_model': 'other.money.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': receipt_id and receipt_id.id or False,
            'domain': [('id', '=', receipt_id.id)],
        }

    state = fields.Selection([
                          ('draft', u'未付款'),
                          ('done', u'已付款'),
                          ('cancel', u'已取消')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    date = fields.Date(string=u'日期', default=lambda self: fields.Date.context_today(self))
    name = fields.Char(string=u'单据编号', copy=False, readonly=True, default='/')
    type = fields.Selection(TYPE_PAY_SELECTION, string=u'付款状态')
    line_ids = fields.One2many('purchase.sale.fee.order.line', 'fee_id', string=u'采购销售费用清单行')

class purchase_sale_fee_order_line(models.Model):
    _name = 'purchase.sale.fee.order.line'
    _description = u'采购销售费用清单明细'

    state = fields.Selection([
                          ('draft', u'未付款'),
                          ('done', u'已付款'),
                          ('cancel', u'已取消')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    fee_id = fields.Many2one('purchase.sale.fee.order', string=u'采购销售费用清单')
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    pay_type = fields.Char(string=u'支出类别')
    amount = fields.Float(string=u'金额')
    unpaid_amount = fields.Float(string=u'未付费用')
    source_id = fields.Char(string=u'源单')
    other_payment_list = fields.Char(string=u'其他支出单编号')
    source_date = fields.Date(string=u'源单日期')
