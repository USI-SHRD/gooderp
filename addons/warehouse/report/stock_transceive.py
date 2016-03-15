# -*- coding: utf-8 -*-

from openerp import tools
from openerp.osv import fields
from openerp.osv import osv
import openerp.addons.decimal_precision as dp


class report_stock_transceive(osv.osv):
    _name = 'report.stock.transceive'
    _auto = False

    _columns = {
        'goods': fields.char(u'产品'),
        'uom': fields.char(u'单位'),
        'lot': fields.char(u'批次'),
        'warehouse': fields.char(u'仓库'),
        'goods_qty_begain': fields.float('期初数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_begain': fields.float(u'期初成本', digits_compute=dp.get_precision('Accounting')),
        'goods_qty_end': fields.float('期末数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_end': fields.float(u'期末成本', digits_compute=dp.get_precision('Accounting')),
        'goods_qty_out': fields.float('出库数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_out': fields.float(u'出库成本', digits_compute=dp.get_precision('Accounting')),
        'goods_qty_in': fields.float('入库数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_in': fields.float(u'入库成本', digits_compute=dp.get_precision('Accounting')),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_transceive')
        print '-----self------', self
        raise osv.exept_osv('fsd', 'fds')
        cr.execute(
            """
            create or replace view report_stock_transceive as (
                SELECT min(line.id) as id,
                       goods.name as goods,
                       line.lot as lot,
                       uom.name as uom,
                       wh.name as warehouse,
                       sum(line.qty_remaining) as goods_qty_begain,
                       sum(line.subtotal) as cost_begain

                FROM wh_move_line line
                LEFT JOIN warehouse wh ON line.warehouse_dest_id = wh.id
                LEFT JOIN goods goods ON line.goods_id = goods.id
                    LEFT JOIN uom uom ON goods.uom_id = uom.id

                WHERE line.qty_remaining > 0
                  AND wh.type = 'stock'
                  AND line.state = 'done'

                GROUP BY wh.name, line.lot, goods.name, uom.name

                ORDER BY goods.name, wh.name, goods_qty_begain asc
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
