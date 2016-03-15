# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class report_stock_transceive_wizard(osv.osv_memory):
    _name = 'report.stock.transceive.wizard'

    _columns = {
        'date_start': fields.date(u'开始期间'),
        'date_end': fields.date(u'结束期间'),
    }

    def open_report(self, cr, uid, ids, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'report.stock.transceive',
            'view_mode': 'tree',
            'name': u'商品收发明细表',
            'context': {'sfd': 'fsd'},
        }
