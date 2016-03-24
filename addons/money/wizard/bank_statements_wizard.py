# -*- coding: utf-8 -*-
from openerp.exceptions import except_orm
from openerp import fields, models, api

class partner_statements_report_wizard(models.Model):
    _name = "bank.statements.report.wizard"
    _description = u"现金银行报表向导"

    from_date = fields.Date(string=u'开始日期')
    end_date = fields.Date(string=u'结束日期')

    @api.multi
    def confirm_bank_statements(self):
        # 现金银行报表
        if self.from_date > self.end_date:
            raise except_orm(u'错误！', u'结束日期不能小于开始日期！')

        resource_id = self.env['ir.model.data'].xmlid_to_res_id('money.bank_statements_report_tree')

        return {
                'name': u'现金银行报表',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'bank.statements.report',
                'view_id': False,
                'views': [(resource_id, 'tree')],
                'type': 'ir.actions.act_window',
                'domain':[('date','>=', self.from_date), ('date','<=', self.end_date)]
                }
