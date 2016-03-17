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

class other_money_type(models.Model):
    _name = 'other.money.type'
    _description = u'支出类别/收入类别'

    type = fields.Char(string=u'类型',size=128, default=lambda self: self._context.get('type'))
    name = fields.Char(string=u'描述',size=128,required=True)

class other_money_order(models.Model):
    _name = 'other.money.order'
    _description = u'其他应收款/应付款'

    TYPE_SELECTION = [
        ('other_pay', u'其他应付款'),
        ('other_get', u'其他应收款'),
    ]

    @api.model
    def create(self, values):
        # 创建单据时，更新订单类型的不同，生成不同的单据编号
        if self._context.get('type') == 'other_get':
            values.update({'name': self.env['ir.sequence'].get('other_receipt_order') or '/'})
        if self._context.get('type') == 'other_pay' and values.get('name', '/') == '/':
            values.update({'name': self.env['ir.sequence'].get('other_payment_order') or '/'})

        return super(other_money_order, self).create(values)

    @api.one
    @api.depends('line_ids.amount')
    def _compute_total_amount(self):
        # 计算应付金额/应收金额
        self.total_amount = sum(line.amount for line in self.line_ids)

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                          ('cancel', u'已取消')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    date = fields.Date(string=u'单据日期', default=lambda self: fields.Date.context_today(self))
    name = fields.Char(string=u'单据编号', copy=False, readonly=True, default='/')
    total_amount = fields.Float(string=u'金额', compute='_compute_total_amount')
    bank_id = fields.Many2one('bank.account', string=u'结算账户')
    line_ids = fields.One2many('other.money.order.line', 'other_money_id', string=u'收支单行')
    type = fields.Selection(TYPE_SELECTION, string=u'其他应收款/应付款')

    @api.multi
    def print_other_money_order(self):
        '''打印 其他收入/支出单'''
        assert len(self._ids) == 1, '一次执行只能有一个id'
        return self.env['report'].get_action('money.report_other_money_order')

class other_money_order_line(models.Model):
    _name = 'other.money.order.line'
    _description = u'其他应收应付明细'

    other_money_id = fields.Many2one('other.money.order', string=u'其他收入/支出')
    other_money_type = fields.Many2one('other.money.type', string=u'类别')
    amount = fields.Float(string=u'金额')
    note = fields.Char(string=u'备注')