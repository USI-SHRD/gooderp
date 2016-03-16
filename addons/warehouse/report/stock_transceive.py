# -*- coding: utf-8 -*-

from openerp import tools
from openerp.osv import fields
from openerp.osv import osv
import openerp.addons.decimal_precision as dp


class report_stock_transceive(osv.osv):
    _name = 'report.stock.transceive'

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
