# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
from datetime import date, timedelta


class report_stock_transceive_wizard(osv.osv_memory):
    _name = 'report.stock.transceive.wizard'

    def onchange_date(self, cr, uid, ids, date_start, date_end):
        if date_start and date_end and date_end < date_start:
            return {'warning': {
                'title': u'错误',
                'message': u'结束日期不可以小于开始日期'
            }, 'value': {'date_end': date_start}}

        return {}

    _columns = {
        'date_start': fields.date(u'开始日期'),
        'date_end': fields.date(u'结束日期'),
        'warehouse': fields.char(u'仓库'),
        'goods': fields.char(u'产品')
    }

    def _default_date_start(self, cr, uid, context=None):
        return date.today().replace(day=1).strftime('%Y-%m-%d')

    def _default_date_end(self, cr, uid, context=None):
        now = date.today()
        next_month = now.month == 12 and now.replace(year=now.year + 1,
            month=1, day=1) or now.replace(month=now.month + 1, day=1)

        return (next_month - timedelta(days=1)).strftime('%Y-%m-%d')

    _defaults = {
        'date_start': _default_date_start,
        'date_end': _default_date_end,
    }

    def open_report(self, cr, uid, ids, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'report.stock.transceive',
            'view_mode': 'tree',
            'name': u'商品收发明细表',
            'context': self.read(cr, uid, ids[0], ['date_start', 'date_end', 'warehouse', 'goods'], context=context),
        }
