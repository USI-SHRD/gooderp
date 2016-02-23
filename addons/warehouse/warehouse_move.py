# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class warehouse_move(osv.osv):
    _name = 'warehouse_move'
    _rec_name = 'goods_id'

    _columns = {
        'picking_id': fields.many2one('warehouse.picking', string=u'移库单'),
        'goods_id': fields.many2one('goods', string=u'产品'),
        # 'lot_id': fields.one2many('warehouse.lot', string=u'批次'),
        'uom_id': fields.many2one('uom', string=u'单位'),
        'warehouse_id': fields.many2one('warehouse', string=u'仓库'),
        'warehouse_dest_id': fields.many2one('warehouse', string=u'目标仓库'),
        'product_qty': fields.float(u'数量', digits_compute=dp.get_precision('Product Quantity')),
        'price': fields.float(u'单价', digits_compute=dp.get_precision('Accounting')),
        'price_subtotal': fields.float(u'金额', digits_compute=dp.get_precision('Accounting')),
        'note': fields.text(u'备注'),
    }
