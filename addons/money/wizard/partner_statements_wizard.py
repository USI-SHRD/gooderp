# -*- coding: utf-8 -*-
from openerp.exceptions import except_orm
from openerp import fields, models, api

class partner_statements_report_wizard(models.Model):
    _name = "partner.statements.report.wizard"
    _description = u"业务伙伴对账单向导"

    partner_id = fields.Many2one('partner', string=u'业务伙伴')
    from_date = fields.Date(string=u'开始日期')
    end_date = fields.Date(string=u'结束日期')
 
    @api.multi
    def confirm_partner_statements(self):
        # 客户对账单
        if self.from_date > self.end_date:
            raise except_orm(u'错误！', u'结束日期不能小于开始日期！')

        resource_id = self.env['ir.model.data'].xmlid_to_res_id('money.partner_statements_report_tree') 

        return {
                'name': u'客户对账单',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'partner.statements.report',
                'view_id': False,
                'views': [(resource_id, 'tree')],
                'type': 'ir.actions.act_window',
                'domain':[('partner_id','=', self.partner_id.id), ('date','>=', self.from_date), ('date','<=', self.end_date)]
                }
