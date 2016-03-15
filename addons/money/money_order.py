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

class money_order(models.Model):
    _name = 'money.order'
    _description = u"收款单/付款单"

    TYPE_SELECTION = [
        ('payables', u'应付款'),
        ('receipts', u'应收款'),
    ]

    @api.model
    def create(self, values):
        if not values.get('name') and self._context.get('default_receipt'):
            values.update({'name': self.pool['ir.sequence'].get(self._cr, self._uid, 'receipt_order', context=self._context) or '/'})
        if not values.get('name') and self._context.get('default_payment'):
            values.update({'name': self.pool['ir.sequence'].get(self._cr, self._uid, 'payment_order', context=self._context) or '/'})
 
        if self._context.get('default_payment'):
            values.update({'type': 'payables'})
        if self._context.get('default_receipt'):
            values.update({'type': 'receipts'})
 
        return super(money_order, self).create(values)

    @api.one
    @api.depends('discount_amount', 'line_ids.amount', 'source_ids.this_reconcile')
    def _compute_advance_payment(self):
        amount, this_reconcile = 0.0, 0.0
        for line in self.line_ids:
            amount += line.amount
        for line in self.source_ids:
            this_reconcile += line.this_reconcile
        self.advance_payment = amount - this_reconcile + self.discount_amount

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                          ('cancel', u'已取消')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date(string=u'单据日期', readonly=True, default=lambda self: fields.Date.context_today(self), states={'draft': [('readonly', False)]})
    name = fields.Char(string=u'单据编号', copy=False, readonly=True)
    note = fields.Text(string=u'备注', readonly=True, states={'draft': [('readonly', False)]})
    discount_amount = fields.Float(string=u'整单折扣', readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('money.order.line', 'money_id', string=u'收支单行', readonly=True, states={'draft': [('readonly', False)]})
    source_ids = fields.One2many('source.order.line', 'money_id', string=u'源单行', readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection(TYPE_SELECTION, string=u'应收款/应付款')
    advance_payment = fields.Float(string=u'本次预收款', store=True, compute='_compute_advance_payment')

    @api.multi
    def button_select_source_order(self):
        if not self._ids:
            return
  
        dummy, view_id = self.pool['ir.model.data'].get_object_reference(self._cr, self._uid, 'money', 'source_order_line_tree')
#         line_ini = self.browse(self._cr, self._uid, ids[0], context=context)
#         return {
#             'name': u'选择源单',
#             'view_mode': 'tree',
#             'view_id': view_id,
#             'view_type': 'tree',
#             'res_model': 'source.order.line',
#             'type': 'ir.actions.act_window',
#             'nodestroy': True,
#             'target': 'new',
#             'domain': '[]',
#             'context': {
# #                 'payment_expected_currency': inv.currency_id.id,
#             }
#         }
        return

    @api.multi
    def money_approve(self):
        '''对收支单的提交审核按钮，还需修改'''
        self.write({'state': 'done'})
        return True

    @api.multi
    def money_action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def print_money_order(self):
        return True

class money_order_line(models.Model):
    _name = 'money.order.line'
    _description = u'收支单明细'

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                          ('cancel', u'已取消')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    money_id = fields.Many2one('money.order',string=u'收款单')
    bank_id =  fields.Many2one('bank.account', string=u'结算账户')
    amount = fields.Float(string=u'收/付款金额')
    mode_id = fields.Many2one('settle.mode', string=u'结算方式')
    number =  fields.Char(string=u'结算号')
    note = fields.Char(string=u'备注')

class money_invoice(models.Model):
    _name = 'money.invoice'
    _description = u'源单'

    name = fields.Char(string=u'订单编号', copy=False)
    type = fields.Char(string=u'源单类型')
    business_type = fields.Char(string=u'业务类别')
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')

class source_order_line(models.Model):
    _name = 'source.order.line'
    _description = u'源单明细'

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                          ('cancel', u'已取消')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    money_id = fields.Many2one('money.order', string=u'收款单')
    name = fields.Many2one('money.invoice', string=u'源单编号', copy=False)
    business_type = fields.Char(string=u'业务类别') # 
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    this_reconcile = fields.Float(string=u'本次核销金额')
