# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class wh_move_line(osv.osv):
    _name = 'wh.move.line'
    _rec_name = 'goods_id'

    MOVE_LINE_TYPE = [
        ('out', u'出库'),
        ('in', u'入库'),
    ]

    def _get_default_warehouse(self, cr, uid, context=None):
        context = context or {}
        if context.get('warehouse_type'):
            return self.pool.get('warehouse').get_warehouse_by_type(cr, uid, context.get('warehouse_type'))

        return False

    def _get_default_warehouse_dest(self, cr, uid, context=None):
        context = context or {}
        if context.get('warehouse_dest_type'):
            return self.pool.get('warehouse').get_warehouse_by_type(cr, uid, context.get('warehouse_dest_type'))

        return False

    _columns = {
        'move_id': fields.many2one('wh.move', string=u'移库单'),
        'type': fields.selection(MOVE_LINE_TYPE, u'类型'),
        'goods_id': fields.many2one('goods', string=u'产品'),
        'lot_id': fields.one2many('wh.lot', 'line_id', string=u'批次'),
        'production_date': fields.date(u'生产日期'),
        'shelf_life': fields.integer(u'保质期(天)'),
        'valid_date': fields.date(u'有效期至'),
        'uom_id': fields.many2one('uom', string=u'单位'),
        'warehouse_id': fields.many2one('warehouse', string=u'调出仓库'),
        'warehouse_dest_id': fields.many2one('warehouse', string=u'调入仓库'),
        'goods_qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity')),
        'price': fields.float(u'单价', digits_compute=dp.get_precision('Accounting')),
        'price_subtotal': fields.float(u'金额', digits_compute=dp.get_precision('Accounting')),
        'note': fields.text(u'备注'),
    }

    _defaults = {
        'type': lambda self, cr, uid, ctx=None: ctx.get('type'),
        'warehouse_id': _get_default_warehouse,
        'warehouse_dest_id': _get_default_warehouse_dest,
    }
