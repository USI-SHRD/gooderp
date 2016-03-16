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
        assert(len(self._ids) == 1)
        res = self.env['ir.model.data'].get_object_reference('money', 'money_invoice_tree')
        view_id = res and res[1] or False
        print "view_id", view_id
        # 选择源单
        dict, ret = [], []


        return {
            'name': u'选择源单',
            'view_type': 'tree',
            'view_mode': 'tree',
            'view_id': False,
            'views': [(view_id, 'tree')],
            'res_model': 'money.invoice',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': [],
        }

    @api.multi
    def money_approve(self):
        '''对收支单的提交审核按钮，还需修改'''
        self.write({'state': 'done'})
        return True

    @api.multi
    def money_action_draft(self):
        self.write({'state': 'draft'})
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
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    money_id = fields.Many2one('money.order',string=u'收款单')
    bank_id =  fields.Many2one('bank.account', string=u'结算账户')
    amount = fields.Float(string=u'金额')
    mode_id = fields.Many2one('settle.mode', string=u'结算方式')
    number =  fields.Char(string=u'结算号')
    note = fields.Char(string=u'备注')

# 测试类
class invoice(models.Model):
    _name = 'invoice'
    _description = u'关联到源单'
    invoice_ids = fields.One2many('money.invoice', 'invoice_id', string=u'源单')

class money_invoice(models.Model):
    _name = 'money.invoice'
    _description = u'源单'

    invoice_id = fields.Many2one('invoice', string=u'关联到源单')
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    name = fields.Char(string=u'订单编号', copy=False, required=True)
    type = fields.Char(string=u'源单类型')
    business_type = fields.Char(string=u'业务类别')
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    date_due = fields.Date(string=u'到期日')

class source_order_line(models.Model):
    _name = 'source.order.line'
    _description = u'源单明细'

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                          ('cancel', u'已取消')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    money_id = fields.Many2one('money.order', string=u'收款单')
    name = fields.Many2one('money.invoice', string=u'源单编号', copy=False)
    business_type = fields.Char(string=u'业务类别') # 
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    this_reconcile = fields.Float(string=u'本次核销金额')
    date_due = fields.Date(string=u'到期日')
