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
    _description = u"收付款单"

    TYPE_SELECTION = [
        ('pay', u'付款'),
        ('get', u'收款'),
    ]

    @api.model
    def create(self, values):
        # 创建单据时，更新订单类型的不同，生成不同的单据编号
        if self._context.get('type') == 'get':
            values.update({'name': self.env['ir.sequence'].get('pay.order') or '/'})
        if self._context.get('type') == 'pay':
            values.update({'name': self.env['ir.sequence'].get('get.order') or '/'})

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
        self.amount = amount

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date(string=u'单据日期', readonly=True, default=lambda self: fields.Date.context_today(self), states={'draft': [('readonly', False)]})
    name = fields.Char(string=u'单据编号', copy=False, readonly=True)
    note = fields.Text(string=u'备注', readonly=True, states={'draft': [('readonly', False)]})
    discount_amount = fields.Float(string=u'整单折扣', readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('money.order.line', 'money_id', string=u'收付款单行', readonly=True, states={'draft': [('readonly', False)]})
    source_ids = fields.One2many('source.order.line', 'money_id', string=u'源单行', readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection(TYPE_SELECTION, string=u'类型', default=lambda self: self._context.get('type'))
    amount = fields.Float(string=u'总金额', store=True, compute='_compute_advance_payment')
    advance_payment = fields.Float(string=u'本次预收款', store=True, compute='_compute_advance_payment')
    to_reconcile = fields.Float(string=u'未核销预收款')
    reconciled = fields.Float(string=u'已核销预收款')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id:
            return {}
        source_lines = []
        self.source_ids = []
        print "self", self.type, self._context.get('type')
        if self.env.context.get('type') == 'get':
            money_invoice = self.env['money.invoice'].search([('partner_id', '=', self.partner_id.id),
                                                              ('category_id.type', '=', 'receipt'),
                                                              ('to_reconcile', '>', 0)])
        if self.env.context.get('type') == 'pay':
            money_invoice = self.env['money.invoice'].search([('partner_id', '=', self.partner_id.id),
                                                              ('category_id.type', '=', 'payment'),
                                                              ('to_reconcile', '>', 0)])
        for invoice in money_invoice:
            source_lines.append({
                   'name': invoice.id,
                   'category_id': invoice.category_id.id,
                   'amount': invoice.amount,
                   'date': invoice.date,
                   'reconciled': invoice.reconciled,
                   'to_reconcile': invoice.to_reconcile,
                   'this_reconcile': invoice.to_reconcile,
                   'date_due': invoice.date_due,
                   })
        self.source_ids = source_lines

    @api.multi
    def money_order_done(self):
        '''对收支单的审核按钮'''
        if self.advance_payment < 0:
            raise except_orm(u'错误', u'核销金额不能大于付款金额')

        self.to_reconcile = self.advance_payment
        self.reconciled = self.amount - self.advance_payment

        total = 0
        for line in self.line_ids:
            if self.type == 'pay': # 付款账号余额减少
                if line.bank_id.balance < line.amount:
                    raise except_orm(u'错误', u'账户余额不足')
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
            if source.to_reconcile < source.this_reconcile:
                raise except_orm(u'错误', u'本次核销金额不能大于未核销金额')
            source.name.to_reconcile = source.to_reconcile - source.this_reconcile
            source.name.reconciled = source.reconciled + source.this_reconcile
        self.state = 'done'
        return True

    @api.multi
    def money_order_draft(self):
        self.to_reconcile = 0
        self.reconciled = 0

        total = 0
        for line in self.line_ids:
            if self.type == 'pay': # 付款账号余额减少
                line.bank_id.balance += line.amount
            else: # 收款账号余额增加
                if line.bank_id.balance < line.amount:
                    raise except_orm(u'错误', u'账户余额不足')
                line.bank_id.balance -= line.amount
            total += line.amount

        if self.type == 'pay':
            self.partner_id.payable += total
        else:
            self.partner_id.receivable += total

        # 更新源单的未核销金额、已核销金额
        for source in self.source_ids:
            source.name.to_reconcile = source.to_reconcile + source.this_reconcile
            source.name.reconciled = source.reconciled - source.this_reconcile
        self.state = 'draft'
        return True

    @api.multi
    def print_money_order(self):
        return True

class money_order_line(models.Model):
    _name = 'money.order.line'
    _description = u'收付款单明细'

    money_id = fields.Many2one('money.order',string=u'收付款单')
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
    category_id = fields.Many2one('core.category', string=u'类别')
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    date_due = fields.Date(string=u'到期日')

    @api.multi
    def money_invoice_done(self):
        for inv in self:
            inv.state = 'done'
            inv.to_reconcile = inv.amount
            if self.category_id.type == 'income':
                inv.partner_id.receivable += inv.amount
            if self.category_id.type == 'expense':
                inv.partner_id.payable += inv.amount

    @api.multi
    def money_invoice_draft(self):
        for inv in self:
            inv.state = 'draft'
            inv.to_reconcile = 0
            if self.category_id.type == 'income':
                inv.partner_id.receivable -= inv.amount
            if self.category_id.type == 'expense':
                inv.partner_id.payable -= inv.amount
        
class source_order_line(models.Model):
    _name = 'source.order.line'
    _description = u'源单明细'

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    money_id = fields.Many2one('money.order', string=u'收款单')
    reconcile_id = fields.Many2one('reconcile.order', string=u'核销单')
    get_reconcile_id = fields.Many2one('reconcile.order', string=u'核销单')
    name = fields.Many2one('money.invoice', string=u'源单编号', copy=False)
    category_id = fields.Many2one('core.category', string=u'类别')
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
        # 生成订单编号
        if values.get('name', '/') == '/':
            values.update({'name': self.env['ir.sequence'].get('reconcile_order') or '/'})

        return super(reconcile_order, self).create(values)

    state = fields.Selection([
                          ('draft', u'未审核'),
                          ('done', u'已审核'),
                           ], string=u'状态', readonly=True, default='draft', copy=False)
    partner_id = fields.Many2one('partner', string=u'客户', required=True)
    to_partner_id = fields.Many2one('partner', string=u'转入客户')
    pay_source_ids = fields.One2many('advance.payment', 'pay_reconcile_id', string=u'预收单行')
    source_ids = fields.One2many('source.order.line', 'reconcile_id', string=u'应收单行')
    get_source_ids = fields.One2many('source.order.line', 'get_reconcile_id', string=u'应收单行')
    business_type = fields.Selection(TYPE_SELECTION, string=u'业务类性') #
    name = fields.Char(string=u'单据编号', copy=False, readonly=True, default='/')
    date = fields.Date(string=u'单据日期', default=lambda self: fields.Date.context_today(self))
    note = fields.Text(string=u'备注', readonly=True)

    @api.multi
    def adv_pay_or_get(self, partner_id, money_order):
        result = []
        for payment in money_order:
            res = {
                   'name': payment.name,
                   'category_id': payment.type,
                   'amount': payment.advance_payment, # 预收款    预付款
                   'date': payment.date,
                   'reconciled': payment.reconciled, # 已核销预收款
                   'to_reconcile': payment.to_reconcile, # 未核销预收款
                   'this_reconcile': payment.to_reconcile, # 未核销预收款
                   }
            result.append(res)
        return result

    @api.multi
    def rec_get_or_pay(self, partner_id, money_invoice, business_type):
        result = []
        for invoice in money_invoice:
            res = {
                   'name': invoice.id,
                   'type': invoice.type,
                   'category_id': invoice.category_id.id,
                   'amount': invoice.amount, # 应收款     应付款
                   'date': invoice.date,
                   'reconciled': invoice.reconciled, # 已核销应收
                   'to_reconcile': invoice.to_reconcile, # 未核销应收
                   'date_due': invoice.date_due,
                   }
            result.append(res)
        return result

    @api.multi
    def onchange_partner_id(self, partner_id, business_type):
        # 需要继续完善
        if not partner_id or not business_type:
            return {}

        money_order = self.env['money.order']
        money_invoice = self.env['money.invoice']

        if business_type == 'adv_pay_rec_get': # 预收冲应收
            result = {'value': {'pay_source_ids': [], 'get_source_ids': []}}
            money_order = self.env['money.order'].search([('partner_id', '=', partner_id), ('type', '=', 'get'), ('state', '=', 'done'), ('to_reconcile', '!=', 0)]) # 预收
            money_invoice = self.env['money.invoice'].search([('category_id.type', '=', 'income'), ('partner_id', '=', partner_id), ('to_reconcile', '!=', 0)]) # 应收
            res_1 = self.adv_pay_or_get(partner_id, money_order)
            for res in res_1:
                result['value']['pay_source_ids'].append((0, 0, res))
            res_2 = self.rec_get_or_pay(partner_id, money_invoice, business_type)
            for res in res_2:
                result['value']['get_source_ids'].append((0, 0, res))

        if business_type == 'adv_get_rec_pay': # 预付冲应付
            result = {'value': {'pay_source_ids': [], 'get_source_ids': []}}
            money_order = self.env['money.order'].search([('partner_id', '=', partner_id), ('type', '=', 'pay'), ('state', '=', 'done'), ('to_reconcile', '!=', 0)]) # 预付
            money_invoice = self.env['money.invoice'].search([('category_id.type', '=', 'expense'), ('partner_id', '=', partner_id), ('to_reconcile', '!=', 0)]) # 应付
            res_1 = self.adv_pay_or_get(partner_id, money_order)
            for res in res_1:
                result['value']['pay_source_ids'].append((0, 0, res))
            res_2 = self.rec_get_or_pay(partner_id, money_invoice, business_type)
            for res in res_2:
                result['value']['get_source_ids'].append((0, 0, res))

        if business_type == 'get_rec_pay': # 应收冲应付
            result = {'value': {'source_ids': [], 'get_source_ids': []}}
            money_invoice_get = self.env['money.invoice'].search([('category_id.type', '=', 'income'), ('partner_id', '=', partner_id), ('to_reconcile', '!=', 0)]) # 应收
            money_invoice = self.env['money.invoice'].search([('category_id.type', '=', 'expense'), ('partner_id', '=', partner_id), ('to_reconcile', '!=', 0)]) # 应付
            res_1 = self.rec_get_or_pay(partner_id, money_invoice_get, business_type)
            for res in res_1:
                result['value']['source_ids'].append((0, 0, res))
            res_2 = self.rec_get_or_pay(partner_id, money_invoice, business_type)
            for res in res_2:
                result['value']['get_source_ids'].append((0, 0, res))

        if business_type == 'get_to_get': # 应收转应收
            result = {'value': {'get_source_ids': []}}
            money_invoice_get = self.env['money.invoice'].search([('category_id.type', '=', 'income'), ('partner_id', '=', partner_id), ('to_reconcile', '!=', 0)]) # 应收
            res_1 = self.rec_get_or_pay(partner_id, money_invoice_get, business_type)
            for res in res_1:
                result['value']['get_source_ids'].append((0, 0, res))

        if business_type == 'pay_to_pay': # 应付转应付
            result = {'value': {'source_ids': []}}
            money_invoice_get = self.env['money.invoice'].search([('category_id.type', '=', 'expense'), ('partner_id', '=', partner_id), ('to_reconcile', '!=', 0)]) # 应付
            res_1 = self.rec_get_or_pay(partner_id, money_invoice_get, business_type)
            for res in res_1:
                result['value']['source_ids'].append((0, 0, res))

        return result

    @api.multi
    def get_or_pay(self, line, business_type, partner_id, to_partner_id, name):
        if line.this_reconcile > line.to_reconcile:
            raise except_orm(u'错误', u'核销金额不能大于未核销金额')
        # 更新每一行的已核销余额、未核销余额
        line.to_reconcile -= line.this_reconcile
        line.reconciled += line.this_reconcile
        # 更新源单的未核销金额、已核销金额
        if line.to_reconcile == 0:
            line.name.write({'partner_id': self.partner_id.id, 'to_reconcile': 0, 'reconciled': line.reconciled, 'state': 'done'})
        if line.to_reconcile != 0:
            line.name.write({'partner_id': self.partner_id.id, 'to_reconcile': line.to_reconcile, 'reconciled': line.reconciled})

        if business_type in ['get_to_get', 'pay_to_pay']:
            res = {
                   'name': name,
                   'category_id': line.category_id.id,
                   'amount': line.this_reconcile,
                   'date': line.date,
                   'reconciled': 0, # 已核销
                   'to_reconcile': line.this_reconcile, # 未核销
                   'date_due': line.date_due,
                   'partner_id': to_partner_id.id,
                   }
            if business_type == 'get_to_get':
                source_id = self.env['money.invoice'].create(res)
                source_id.partner_id.receivable += line.this_reconcile
                partner_id.receivable -= line.this_reconcile

            if business_type == 'pay_to_pay':
                source_id = self.env['money.invoice'].create(res)
                source_id.partner_id.payable += line.this_reconcile
                partner_id.payable -= line.this_reconcile

        return True

    @api.multi
    def reconcile_order_done(self):
        '''核销单的审核按钮'''
        # 核销金额不能大于未核销金额
        pay_total, pay_reconcile, get_reconcile = 0, 0, 0
        for line in self.pay_source_ids:
            pay_total += line.advance_payment
            pay_reconcile += line.this_reconcile

            if line.this_reconcile > line.to_reconcile:
                raise except_orm(u'错误', u'核销金额不能大于未核销金额')
            # 更新每一行的已核销余额、未核销余额
            line.to_reconcile -= line.this_reconcile
            line.reconciled += line.this_reconcile

            # 更新预付款/收款单的未核销金额、已核销金额
            pay_id = self.env['money.order'].search([('name', '=', line.name)])
            if pay_id:
                if line.to_reconcile == 0:
                    pay_id[0].write({'partner_id': self.partner_id.id, 'to_reconcile': 0, 'reconciled': line.reconciled, 'state': 'done'})
                if line.to_reconcile != 0:
                    pay_id[0].write({'partner_id': self.partner_id.id, 'to_reconcile': line.to_reconcile, 'reconciled': line.reconciled})

        for line in self.get_source_ids:
            get_reconcile += line.this_reconcile
            self.get_or_pay(line, self.business_type, self.partner_id, self.to_partner_id, self.name)
        for line in self.source_ids: # 应收
            pay_reconcile += line.this_reconcile
            self.get_or_pay(line, self.business_type, self.partner_id, self.to_partner_id, self.name)

        # 核销金额必须相同
        if self.business_type in ['adv_pay_rec_get', 'adv_get_rec_pay', 'get_rec_pay']:
            if pay_reconcile != get_reconcile:
                raise except_orm(u'错误', u'核销金额必须相同')
        if self.business_type in ['get_to_get', 'pay_to_pay']:
            if self.partner_id.id == self.to_partner_id.id:
                raise except_orm(u'错误', u'转出客户和转入客户不能相同')

        self.state = 'done'
        return True

class advance_payment(models.Model):
    _name = 'advance.payment'
    _description = u'核销单预收付款行'

    pay_reconcile_id = fields.Many2one('reconcile.order', string=u'核销单')
    name = fields.Many2one('money.order', string=u'预付款单编号', copy=False, required=True)
    date = fields.Date(string=u'单据日期')
    amount = fields.Float(string=u'单据金额')
    reconciled = fields.Float(string=u'已核销金额')
    to_reconcile = fields.Float(string=u'未核销金额')
    this_reconcile = fields.Float(string=u'本次核销金额')
