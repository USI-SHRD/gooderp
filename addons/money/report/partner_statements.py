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
    _description = u"业务伙伴对账单"
    _auto = False

    partner_id = fields.Many2one('partner', string=u'业务伙伴', readonly=True)
    name = fields.Char(string=u'单据编号', readonly=True)
    date = fields.Date(string=u'单据日期', readonly=True)
    category_id = fields.Many2one('core.category', string=u'业务类别', readonly=True)
    amount = fields.Float(string=u'单据金额', readonly=True)
    discount_amount = fields.Float(string=u'优惠金额', readonly=True)
    cost = fields.Float(string=u'客户承担费用', readonly=True) # ?
    real_amount = fields.Float(string=u'实际收款金额', readonly=True)
    balance_amount = fields.Float(string=u'应收款余额', readonly=True)
    note = fields.Char(string=u'备注', readonly=True)

    def _select(self):
        # union money_order,money_invoice,other_money_order
        select_str = """
            SELECT  m.id as id,
                    m.partner_id as partner_id,
                    m.name as name,
                    m.date as date,
                    Null as category_id,
                    m.amount as amount,
                    m.discount_amount as discount_amount,
                    0 as cost,
                    m.amount as real_amount,
                    0 as balance_amount,
                    m.note as note
            FROM money_order as m
            UNION
            SELECT  mi.id as id,
                    mi.partner_id as partner_id,
                    mi.name as name,
                    mi.date as date,
                    mi.category_id as category_id,
                    mi.amount as amount,
                    0 as discount_amount,
                    0 as cost,
                    mi.reconciled as real_amount,
                    mi.to_reconcile as balance_amount,
                    Null as note
            FROM money_invoice as mi
            UNION
            SELECT  omo.id as id,
                    omo.partner_id as partner_id,
                    omo.name as name,
                    omo.date as date,
                    NULL as category_id,
                    omo.total_amount as amount,
                    0 as discount_amount,
                    omo.total_amount as cost,
                    omo.total_amount as real_amount,
                    0 as balance_amount,
                    NULL as note
            FROM other_money_order as omo
        """
        return select_str

    # WHERE partner_id = %s and date >= %s and date <= %s
    # '3', '2016-03-21', '2016-03-23', '3', '2016-03-21', '2016-03-23', '3', '2016-03-21', '2016-03-23'

    def init(self, cr):
        # self._table = partner_statements_report
        tools.drop_view_if_exists(cr, 'partner_statements_report')
        cr.execute("""
            CREATE or REPLACE VIEW %s as %s
        """ % ('partner_statements_report', self._select()))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
