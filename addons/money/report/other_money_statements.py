# -*- coding: utf-8 -*-

from openerp import fields, models, api, tools

class other_money_statements_report(models.Model):
    _name = "other.money.statements.report"
    _description = u"其他收支单"
    _auto = False

    date = fields.Date(string=u'日期', readonly=True)
    name = fields.Char(string=u'单据编号', readonly=True)
    type = fields.Char(string=u'收支类别', readonly=True)
    bank_id = fields.Many2one(string=u'收支项目', readonly=True)
    get = fields.Float(string=u'收入', readonly=True)
    pay = fields.Float(string=u'支出', readonly=True)
    partner_id = fields.Many2one('partner', string=u'往来单位', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'other_money_statements_report')
        cr.execute("""
            CREATE or REPLACE VIEW other_money_statements_report as (
            SELECT  omo.id as id,
                    omo.date as date,
                    omo.name as name,
                    (CASE WHEN omo.type = 'other_get' THEN '其他收入' ELSE '其他支出' END) AS type,
                    omo.bank_id as bank_id,
                    (CASE WHEN omo.type = 'other_get' THEN omo.total_amount ELSE 0 END) AS get,
                    (CASE WHEN omo.type = 'other_pay' THEN omo.total_amount ELSE 0 END) AS pay,
                    omo.partner_id as partner_id
            FROM other_money_order as omo
            ORDER BY date)
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
