# -*- coding: utf-8 -*-
from openerp.exceptions import except_orm
from openerp import fields, models, api

class partner_statements_report_wizard(models.Model):
    _name = "partner.statements.report.wizard"
    _description = u"业务伙伴对账单向导"

    @api.model
    def _get_company_start_date(self):
        return self.env.user.company_id.start_date

    partner_id = fields.Many2one('partner', string=u'业务伙伴', required=True)
    from_date = fields.Date(string=u'开始日期', required=True, default=_get_company_start_date)
    to_date = fields.Date(string=u'结束日期', required=True, default=lambda self: fields.Date.context_today(self))

    @api.multi
    def customer_statements_without_goods(self):
        # 客户对账单
        if self.from_date > self.to_date:
            raise except_orm(u'错误！', u'结束日期不能小于开始日期！')
        view = self.env.ref('money.partner_statements_report_tree')

        return {
                'name': u'客户对账单:' + self.partner_id.name,
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'partner.statements.report',
                'view_id': False,
                'views': [(view.id, 'tree')],
                'type': 'ir.actions.act_window',
                'domain':[('partner_id','=',self.partner_id.id), ('date','>=', self.from_date), ('date','<=', self.to_date)]
                }

    @api.multi
    def customer_statements_with_goods(self):
        # 客户对账单
        res_ids = []
        if self.from_date > self.to_date:
            raise except_orm(u'错误！', u'结束日期不能小于开始日期！')
        reports = self.env['partner.statements.report'].search([('partner_id','=',self.partner_id.id),
                                                                ('date','>=', self.from_date),
                                                                ('date','<=', self.to_date)])
        for report in reports:
            res_ids.append(self.env['customer.statements.report.with.goods'].create({
                    'partner_id': report.partner_id.id,
                    'name': report.name,
                    'date': report.date,
                    'sale_amount': report.sale_amount,
                    'benefit_amount': report.benefit_amount,
                    'fee': report.fee,
                    'amount': report.amount,
                    'pay_amount': report.pay_amount,
                    'balance_amount': report.balance_amount,
                    'note': report.note,
                    'move_id': report.move_id.id}).id)

            if report.move_id:
                for line in report.move_id.line_out_ids:
                    res_ids.append(self.env['customer.statements.report.with.goods'].create({
                            'goods_code': line.goods_id.code,
                            'goods_name': line.goods_id.name,
                            'attribute_id': line.attribute_id.id,
                            'uom_id': line.uom_id.id,
                            'quantity': line.goods_qty,
                            'price': line.price,
                            'discount_amount': line.discount_amount,
                            'without_tax_amount': line.amount,
                            'tax_amount': line.tax_amount
                            }).id)

        view = self.env.ref('money.partner_statements_report_with_goods_tree')

        return {
                'name': u'客户对账单:' + self.partner_id.name,
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'customer.statements.report.with.goods',
                'view_id': False,
                'views': [(view.id, 'tree')],
                'type': 'ir.actions.act_window',
                'domain':[('id','in', res_ids)]
                }
