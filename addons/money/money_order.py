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
        ('pay', u'付款'),
        ('get', u'收款'),
    ]

    @api.model
    def create(self, values):
        # 创建单据时，更新订单类型的不同，生成不同的单据编号
        if self._context.get('type') == 'get':
            values.update({'name': self.env['ir.sequence'].get('receipt_order') or '/'})
        if self._context.get('type') == 'pay':
            values.update({'name': self.env['ir.sequence'].get('payment_order') or '/'})

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
    source_ids = fields.One2many('money.invoice', 'money_id', string=u'源单行', readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection(TYPE_SELECTION, string=u'应收款/应付款', default=lambda self: self._context.get('type'))
    advance_payment = fields.Float(string=u'本次预收款', store=True, compute='_compute_advance_payment')

    @api.multi
    def onchange_partner_id(self, partner_id):
        if not partner_id:
            return {}

        res = {}
        result = {'value': {'source_ids': []}}
        money_invoice = self.env['money.invoice'].search([('partner_id', '=', partner_id), ('to_reconcile', '!=', 0)])
        for invoice in money_invoice:
            print "anme", invoice.name, invoice.type
            res = {
                   'name': invoice.name,
                   'type': invoice.type,
                   'business_type': invoice.business_type,
                   'amount': invoice.amount,
                   'date': invoice.date,
                   'reconciled': invoice.reconciled,
                   'to_reconcile': invoice.to_reconcile,
                   'date_due': invoice.date_due,
                   }
            result['value']['source_ids'].append((0, 0, res))
        return result

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
        '''对收支单的审核按钮'''
        total = 0
        for line in self.line_ids:
            line.bank_id.balance += line.amount
            total += line.amount
        if self.type == 'payables':
            self.partner_id.payable -= total
        else:
            self.partner_id.receivable -= total
        self.state = 'done'
        return True

    @api.multi
    def money_action_draft(self):
        self.state = 'draft'
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
    bank_id =  fields.Many2one('bank.account', string=u'结算账户', required=True)
    amount = fields.Float(string=u'金额')
    mode_id = fields.Many2one('settle.mode', string=u'结算方式')
    number =  fields.Char(string=u'结算号')
    note = fields.Char(string=u'备注')

class money_invoice(models.Model):
    _name = 'money.invoice'
    _description = u'源单'

#     @api.one
#     @api.depends('this_reconcile', 'to_reconcile', 'reconciled')
#     def _compute_reconcile(self):
#         print "self.to_reconcile - self.this_reconcile", self.to_reconcile , self.this_reconcile
#         self.to_reconcile = self.to_reconcile - self.this_reconcile
#         self.reconciled = self.reconciled + self.this_reconcile

    state = fields.Selection([
                          ('draft', u'草稿'),
                          ('done', u'完成')
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    name = fields.Char(string=u'订单编号', copy=False, required=True)
    type = fields.Char(string=u'源单类型')
    business_type = fields.Char(string=u'业务类别')
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    date_due = fields.Date(string=u'到期日')
    this_reconcile = fields.Float(string=u'本次核销金额')
    money_id = fields.Many2one('money.order', string=u'收款单')

class source_order_line(models.Model):
    _name = 'source.order.line'
    _description = u'源单明细'

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
#     money_id = fields.Many2one('money.order', string=u'收款单')
    name = fields.Many2one('money.invoice', string=u'源单编号', copy=False)
    business_type = fields.Char(string=u'业务类别') # 
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    this_reconcile = fields.Float(string=u'本次核销金额')
    date_due = fields.Date(string=u'到期日')
