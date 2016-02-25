# -*- coding: utf-8 -*-

from openerp.osv import osv


class goods(osv.osv):
    _inherit = 'goods'

    def get_cost_by_warehouse(self, cr, uid, ids, waerhouse_id, qty, context=None):
        return 1
