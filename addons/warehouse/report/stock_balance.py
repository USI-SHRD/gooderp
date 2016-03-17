# -*- coding: utf-8 -*-

from openerp import tools
from openerp.osv import fields
from openerp.osv import osv
import openerp.addons.decimal_precision as dp


class report_stock_balance(osv.osv):
    _name = 'report.stock.balance'
    _auto = False

    _columns = {
        'goods': fields.char(u'产品'),
        'uom': fields.char(u'单位'),
        'lot': fields.char(u'批次'),
        'warehouse': fields.char(u'仓库'),
        'goods_qty': fields.float('数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost': fields.float(u'成本', digits_compute=dp.get_precision('Accounting')),
    }

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        res = super(report_stock_balance, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=False, lazy=True)

        print '--------------read_group-------------'
        print '   domain', domain
        print '   fields', fields
        print '   groupby', groupby
        print '   offset', offset
        print '   limit', limit
        print '   context', context
        print '   orderby', orderby
        print '   lazy', lazy

        from pprint import pprint
        pprint(res)

        return res

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_balance')
        cr.execute(
            """
            create or replace view report_stock_balance as (
                SELECT min(line.id) as id,
                       goods.name as goods,
                       line.lot as lot,
                       uom.name as uom,
                       wh.name as warehouse,
                       sum(line.qty_remaining) as goods_qty,
                       sum(line.subtotal) as cost

                FROM wh_move_line line
                LEFT JOIN warehouse wh ON line.warehouse_dest_id = wh.id
                LEFT JOIN goods goods ON line.goods_id = goods.id
                    LEFT JOIN uom uom ON goods.uom_id = uom.id

                WHERE line.qty_remaining > 0
                  AND wh.type = 'stock'
                  AND line.state = 'done'

                GROUP BY wh.name, line.lot, goods.name, uom.name

                ORDER BY goods.name, wh.name, goods_qty asc
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
