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
    source_ids = fields.One2many('source.order.line', 'money_id', string=u'源单行', readonly=True, states={'draft': [('readonly', False)]})
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
            res = {
                   'name': invoice.id,
                   'type': invoice.type,
                   'business_type': invoice.business_type,
                   'amount': invoice.amount,
                   'date': invoice.date,
                   'reconciled': invoice.reconciled,
                   'to_reconcile': invoice.to_reconcile,
                   'date_due': invoice.date_due,
                   'partner_id': partner_id,
                   }
            result['value']['source_ids'].append((0, 0, res))
        return result

    @api.multi
    def money_approve(self):
        '''对收支单的审核按钮'''
        if self.advance_payment < 0:
            raise except_orm(u'错误', u'预付款不能小于零')

        total = 0
        for line in self.line_ids:
            if self.type == 'pay': # 付款账号余额减少
                line.bank_id.balance -= line.amount
            else: # 收款账号余额增加
                line.bank_id.balance += line.amount
            total += line.amount

        if self.type == 'pay':
            self.partner_id.payable -= total
        else:
            self.partner_id.receivable -= total

        # 更新源单的未核销金额、已核销金额
        for source in self.source_ids:
            to_reconcile = source.to_reconcile - source.this_reconcile
            reconciled = source.reconciled + source.this_reconcile
            if to_reconcile < 0: # 全部核销且有余额
                source.name.write({'partner_id': self.partner_id.id, 'to_reconcile': 0, 'reconciled': reconciled, 'state': 'done'})
            if to_reconcile > 0: # 未全部核销
                source.name.write({'partner_id': self.partner_id.id, 'to_reconcile': to_reconcile, 'reconciled': reconciled})
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

class source_order_line(models.Model):
    _name = 'source.order.line'
    _description = u'源单明细'

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    money_id = fields.Many2one('money.order', string=u'收款单')
    pay_reconcile_id = fields.Many2one('reconcile.order', string=u'核销单')
    get_reconcile_id = fields.Many2one('reconcile.order', string=u'核销单')
    name = fields.Many2one('money.invoice', string=u'源单编号', copy=False)
    business_type = fields.Char(string=u'业务类别') # 
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    this_reconcile = fields.Float(string=u'本次核销金额')
    date_due = fields.Date(string=u'到期日')

class reconcile_order(models.Model):
    _name = 'reconcile.order'
    _description = u'核销单'

    TYPE_SELECTION = [
        ('adv_pay_rec_get', u'预收冲应收'),
        ('adv_get_rec_pay', u'预付冲应付'),
        ('get_rec_pay', u'应收冲应付'),
        ('get_to_get', u'应收转应收'),
        ('pay_to_pay', u'应付转应付'),
    ]

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values.update({'name': self.env['ir.sequence'].get('reconcile_order') or '/'})

        return super(reconcile_order, self).create(values)

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    pay_source_ids = fields.One2many('source.order.line', 'pay_reconcile_id', string=u'预收单行')
    get_source_ids = fields.One2many('source.order.line', 'get_reconcile_id', string=u'应收单行')
    business_type = fields.Selection(TYPE_SELECTION, string=u'业务类性') #
    name = fields.Char(string=u'单据编号', copy=False, readonly=True, default='/')
    date = fields.Date(string=u'单据日期', default=lambda self: fields.Date.context_today(self))
    note = fields.Text(string=u'备注', readonly=True)

    @api.multi
    def onchange_partner_id(self, partner_id, business_type):
        # 需要继续完善
        if not partner_id or not business_type:
            return {}

        res = {}
        money_order_obj = self.env['money.order']
        result = {'value': {'pay_source_ids': [], 'get_source_ids': []}}
        if business_type == 'adv_pay_rec_get': # 预收冲应收
            money_order = money_order_obj.search([('partner_id', '=', partner_id), ('type', '=', 'get'), ('state', '=', 'done')]) # 预收
#         money_invoice = self.env['money.invoice'].search([('partner_id', '=', partner_id), ('business_type', '=', '普通销售'), ('to_reconcile', '!=', 0)]) # 应付

        for money in money_order:
            res = {
#                    'name': money.id,
                   'type': money.type,
                   'business_type': money.type,
                   'amount': money.advance_payment, # 预收款
                   'date': money.date,
                   'reconciled': money.advance_pay_reconciled, # 已核销预收款
                   'to_reconcile': money.advance_payment - money.advance_pay_reconciled, # 未核销预收款
                   'partner_id': partner_id,
                   'date_due': money.date,
                   }
            result['value']['pay_source_ids'].append((0, 0, res))
        
#         for invoice in money_invoice:
#             res = {
#                    'name': invoice.id,
#                    'type': invoice.type,
#                    'business_type': invoice.business_type,
#                    'amount': invoice.amount,
#                    'date': invoice.date,
#                    'reconciled': invoice.reconciled,
#                    'to_reconcile': invoice.to_reconcile,
#                    'date_due': invoice.date_due,
#                    'partner_id': partner_id,
#                    }
#             result['value']['get_source_ids'].append((0, 0, res))
        return result

    @api.multi
    def reconcile_approve(self):
        '''核销单的审核按钮'''
        pay_total = sum(line.amount for line in self.pay_source_ids)
        get_total = sum(line.amount for line in self.get_source_ids)

        if pay_total != get_total:
            raise except_orm(u'错误', u'核销金额必须相同')
        self.state = 'done'
        return True
