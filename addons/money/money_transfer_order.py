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

class money_transfer_order(models.Model):
    _name = 'money.transfer.order'
    _description = u'资金转账单'

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values.update({'name': self.pool['ir.sequence'].get(self._cr, self._uid, 'money_transfer_order', context=self._context) or '/'})

        return super(money_transfer_order, self).create(values)

    name = fields.Char(string=u'单据编号', copy=False, default='/')
    date = fields.Date(string=u'单据日期', default=lambda self: fields.Date.context_today(self))
    note = fields.Text(string=u'备注')
    line_ids = fields.One2many('money.transfer.order.line', 'transfer_id', string=u'资金转账单行')

class money_transfer_order_line(models.Model):
    _name = 'money.transfer.order.line'
    _description = u'资金转账单明细'

    transfer_id = fields.Many2one('money.transfer.order', string=u'资金转账单')
    out_bank_id = fields.Many2one('bank.account', string=u'转出账户') #
    in_bank_id = fields.Many2one('bank.account', string=u'转入账户') #
    amount = fields.Float(string=u'金额')
    mode_id = fields.Many2one('settle.mode', string=u'结算方式')
    number = fields.Char(string=u'结算号') #
    note = fields.Char(string=u'备注')