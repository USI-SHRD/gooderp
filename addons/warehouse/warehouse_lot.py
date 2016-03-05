# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class wh_lot(osv.osv):
    _name = 'wh.lot'

    _columns = {
        'name': fields.char(u'序列号'),
        'line_id': fields.many2one('wh.move.line', u'库存调拨'),
        'goods_id': fields.related('line_id', 'goods_id', type='many2one', relation='goods', string=u'产品'),
        'warehouse_id': fields.related('line_id', 'warehouse_id', type='many2one', relation='warehouse', string=u'仓库'),
        'goods_qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity')),
        'note': fields.text(u'备注'),
    }
