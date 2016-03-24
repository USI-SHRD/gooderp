# -*- coding: utf-8 -*-
from openerp import fields, models, api, tools

class bank_statements_report(models.Model):
    _name = "bank.statements.report"
    _description = u"现金银行报表"
    _auto = False
    _order = 'date desc'

    bank_id = fields.Many2one('bank.account', string=u'账户编号', readonly=True)
    bank_name = fields.Char(string=u'账户名称', readonly=True)
    date = fields.Date(string=u'日期', readonly=True)
    name = fields.Char(string=u'单据名称', readonly=True)
    type = fields.Char(string=u'业务类型', readonly=True)
    get = fields.Float(string=u'收入', readonly=True)
    pay = fields.Float(string=u'支出', readonly=True)
    balance = fields.Float(string=u'账户余额', readonly=True)
    partner_id = fields.Many2one('partner', string=u'往来伙伴', readonly=True)
    note = fields.Char(string=u'备注', readonly=True)

    def init(self, cr):
        # union money_order,other_money_order,money_transfer_order
        tools.drop_view_if_exists(cr, 'bank_statements_report')
        cr.execute("""
            CREATE or REPLACE VIEW bank_statements_report as (
            SELECT  mol.id as id,
                    ba.id as bank_id,
                    ba.name as bank_name,
                    mol.write_date as date,
                    mo.name as name,
                    mo.type as type,
                    (CASE WHEN mo.type = 'get' THEN mol.amount ELSE 0 END) AS get,
                    (CASE WHEN mo.type = 'pay' THEN mol.amount ELSE 0 END) AS pay,
                    ba.balance as balance,
                    mo.partner_id as partner_id,
                    mol.note as note
            FROM money_order_line as mol
            LEFT JOIN money_order as mo ON mol.money_id = mo.id
            LEFT JOIN bank_account as ba ON mol.bank_id = ba.id
            UNION ALL
            SELECT  omo.id as id,
                    ba.id as bank_id,
                    ba.name as bank_name,
                    omo.write_date as date,
                    omo.name as name,
                    omo.type as type,
                    (CASE WHEN omo.type = 'other_get' THEN omo.total_amount ELSE 0 END) AS get,
                    (CASE WHEN omo.type = 'other_pay' THEN omo.total_amount ELSE 0 END) AS pay,
                    ba.balance as balance,
                    omo.partner_id as partner_id,
                    NULL as note
            FROM other_money_order as omo
            LEFT JOIN bank_account as ba ON omo.bank_id = ba.id
            UNION ALL
            SELECT  mtol.id as id,
                    ba.id as bank_id,
                    ba.name as bank_name,
                    mtol.write_date as date,
                    mto.name as name,
                    NULL as type,
                    0 as get,
                    mtol.amount AS pay,
                    ba.balance as balance,
                    NULL as partner_id,
                    mto.note as note
            FROM money_transfer_order_line as mtol
            LEFT JOIN money_transfer_order as mto ON mtol.transfer_id = mto.id
            LEFT JOIN bank_account as ba ON mtol.out_bank_id = ba.id
            UNION ALL
            SELECT  mtol.id as id,
                    ba.id as bank_id,
                    ba.name as bank_name,
                    mtol.write_date as date,
                    mto.name as name,
                    NULL as type,
                    mtol.amount AS get,
                    0 as pay,
                    ba.balance as balance,
                    NULL as partner_id,
                    mto.note as note
            FROM money_transfer_order_line as mtol
            LEFT JOIN money_transfer_order as mto ON mtol.transfer_id = mto.id
            LEFT JOIN bank_account as ba ON mtol.in_bank_id = ba.id
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
