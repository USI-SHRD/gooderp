# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import fields, models, api, tools

class partner_statements_report(models.Model):
    _name = "partner.statements.report"
    _description = u"客户对账单"
    _auto = False
    _order = 'date'

    @api.one
    @api.depends('amount', 'pay_amount')
    def _compute_balance_amount(self):
        # ???
        balance = self.search([('id', '=', self._ids[0] - 1)])
        before_balance = balance.balance_amount
        self.balance_amount += before_balance + self.amount - self.pay_amount

    partner_id = fields.Many2one('partner', string=u'业务伙伴', readonly=True)
    name = fields.Char(string=u'单据编号', readonly=True)
    date = fields.Date(string=u'单据日期', readonly=True)
    type = fields.Char(string=u'业务类别', readonly=True)
    amount = fields.Float(string=u'应收金额', readonly=True)
    pay_amount = fields.Float(string=u'付款金额', readonly=True)
    balance_amount = fields.Float(string=u'应收款余额', compute='_compute_balance_amount', readonly=True)
#     balance_amount = fields.Float(string=u'应收款余额', readonly=True)
    note = fields.Char(string=u'备注', readonly=True)

    def init(self, cr):
        # union money_order,money_invoice,other_money_order
        tools.drop_view_if_exists(cr, 'partner_statements_report')
        cr.execute("""
            CREATE or REPLACE VIEW partner_statements_report as (
            SELECT  ROW_NUMBER() OVER() as id,
                    partner_id,
                    name,
                    date,
                    type,
                    amount,
                    pay_amount,
                    balance_amount,
                    note
            FROM
                (SELECT
                        m.partner_id as partner_id,
                        m.name as name,
                        m.date as date,
                        '收款' AS type,
                        0 as amount,
                        m.amount as pay_amount,
                        0 as balance_amount,
                        m.note as note
                FROM money_order as m
                WHERE m.type = 'get'
                UNION ALL
                SELECT
                        mi.partner_id as partner_id,
                        mi.name as name,
                        mi.date as date,
                        '销售' as type,
                        mi.amount as amount,
                        0 as pay_amount,
                        0 as balance_amount,
                        Null as note
                FROM money_invoice as mi
                LEFT JOIN core_category as c ON mi.category_id = c.id
                WHERE c.type = 'income'
                ORDER BY date
                ) AS ps ORDER BY date)
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
