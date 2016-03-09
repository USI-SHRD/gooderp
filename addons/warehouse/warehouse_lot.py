# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class wh_lot(osv.osv):
    _name = 'wh.lot'

    def _get_qty_remaining(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for lot in self.browse(cr, uid, ids, context=None):
            consume_qty = sum(consume_lot.goods_qty for consume_lot in lot.consume_lot_ids if consume_lot.line_id.state == 'done')
            res.update({
                    lot.id: lot.goods_qty - consume_qty,
                })

        return res

    def _get_lot_by_consume(self, cr, uid, ids, context=None):
        return list(set(consume_lot.lot_id.id for consume_lot in self.browse(cr, uid, ids, context=context)))

    def _get_lot_by_line(self, cr, uid, ids, context=None):
        res = set()
        for line in self.browse(cr, uid, ids, context=context):
            for consume_lot in line.consume_lot_ids:
                res.add(consume_lot.lot_id.id)

        return list(res)

    _columns = {
        'name': fields.char(u'序列号'),
        'line_id': fields.many2one('wh.move.line', u'库存调拨'),
        'goods_id': fields.related('line_id', 'goods_id', type='many2one', relation='goods', string=u'产品'),
        'warehouse_id': fields.related('line_id', 'warehouse_dest_id', type='many2one', relation='warehouse', string=u'仓库'),
        'goods_qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity')),
        'consume_lot_ids': fields.one2many('wh.lot.consume', 'lot_id', u'出库消耗批次'),
        'qty_remaining': fields.function(_get_qty_remaining, type='float', string=u'剩余数量',
            digits_compute=dp.get_precision('Goods Quantity'), store={
                'wh.lot': (lambda self, cr, uid, ids, ctx=None: ids, ['goods_qty'], 10),
                'wh.lot.consume': (_get_lot_by_consume, ['line_id', 'goods_qty'], 10),
                'wh.move.line': (_get_lot_by_line, ['consume_lot_ids', 'state'], 10),
            }),
    }

    _defaults = {
        'goods_qty': 1,
    }


class wh_lot_consume(osv.osv):
    _name = 'wh.lot.consume'

    def onchange_lot(self, cr, uid, ids, lot_id, context=None):
        if lot_id:
            lot = self.pool.get('wh.lot').browse(cr, uid, lot_id, context=context)
            return {'value': {'qty_remaining': lot.qty_remaining, 'goods_qty': lot.qty_remaining}}

        return {'value': {'qty_remaining': 0, 'goods_qty': 0}}

    def onchange_qty(self, cr, uid, ids, qty_remaining, goods_qty, context=None):
        if qty_remaining and goods_qty and qty_remaining < goods_qty:
            return {'value': {'goods_qty': qty_remaining}}

        return {}

    _columns = {
        'lot_id': fields.many2one('wh.lot', u'批次', required=True),
        'qty_remaining': fields.float(u'剩余数量', digits_compute=dp.get_precision('Goods Quantity')),
        'line_id': fields.many2one('wh.move.line', u'移库单', required=True),
        'goods_qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity')),
    }
