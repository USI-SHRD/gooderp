# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class warehouse_move(osv.osv):
    _name = 'warehouse.move'
    _rec_name = 'goods_id'

    _columns = {
        'picking_out_id': fields.many2one('warehouse.picking', string=u'移库单'),
        'picking_in_id': fields.many2one('warehouse.picking', string=u'移库单'),
        'goods_id': fields.many2one('goods', string=u'产品'),
        'lot_id': fields.one2many('warehouse.lot', 'move_id', string=u'批次'),
        'production_date': fields.date(u'生产日期'),
        'shelf_life': fields.integer(u'保质期(天)'),
        'valid_date': fields.date(u'有效期至'),
        'uom_id': fields.many2one('uom', string=u'单位'),
        'warehouse_id': fields.many2one('warehouse', string=u'仓库'),
        'warehouse_dest_id': fields.many2one('warehouse', string=u'目标仓库'),
        'goods_qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity')),
        'price': fields.float(u'单价', digits_compute=dp.get_precision('Accounting')),
        'price_subtotal': fields.float(u'金额', digits_compute=dp.get_precision('Accounting')),
        'note': fields.text(u'备注'),
    }
