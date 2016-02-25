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

    MOVE_LINE_STATE = [
        ('draft', u'草稿'),
        ('done', u'已审核'),
    ]

    def check_availability(self, cr, uid, ids, context=None):
        pass

    def action_done(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            line.check_availability()
            line.write({'state': 'done'})

    def check_cancel(self, cr, uid, ids, context=None):
        pass

    def action_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            line.check_cancel()
            line.write({'state': 'draft'})

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

    def _get_subtotal_util(self, cr, uid, goods_qty, price, context=None):
        return goods_qty * price

    # def _get_subtotal(self, cr, uid, ids, fields_name, arg, context=None):
    #     res = {}
    #     for line in self.browse(cr, uid, ids, context=context):
    #         res.update({line.id: self._get_subtotal_util(
    #             cr, uid, line.goods_qty, line.price, context=context)})

    #     return res

    def onchange_price_by_out(self, cr, uid, ids, goods_id, warehouse_id, goods_qty, context=None):
        if goods_id and warehouse_id and goods_qty:
            price = self.pool.get('goods').get_cost_by_warehouse(
                cr, uid, goods_id, warehouse_id, goods_id, context=context)

            return {'value': {
                'price': price,
                'subtotal': self._get_subtotal_util(
                    cr, uid, goods_qty, price, context=context)
            }}

        return {}

    def onchange_price_by_in(self, cr, uid, ids, goods_qty, price, context=None):
        if goods_qty and price:
            return {'value': {'subtotal': self._get_subtotal_util(
                cr, uid, goods_qty, price, context=context)}}

        return {}

    def onchange_goods_by_out(self, cr, uid, ids, goods_id, warehouse_id, goods_qty, context=None):
        res = {}
        if goods_id:
            goods = self.pool.get('goods').browse(cr, uid, goods_id, context=context)
            res.update({'uom_id': goods.uom_id.id})

            if warehouse_id and goods_qty:
                price = goods.get_cost_by_warehouse(warehouse_id, goods_qty, context=context)
                res.update({
                        'price': price,
                        'subtotal': self._get_subtotal_util(cr, uid, goods_qty, price, context=context)
                    })

        return {'value': res}

    def onchange_goods_by_in(self, cr, uid, ids, goods_id, context=None):
        if goods_id:
            goods = self.pool.get('goods').browse(cr, uid, goods_id, context=context)
            return {'value': {'uom_id': goods.uom_id.id}}

        return {}

    def onchange_goods_by_internal(self, cr, uid, ids, goods_id, context=None):
        return self.onchange_goods_by_in(cr, uid, ids, goods_id, context=context)

    _columns = {
        'move_id': fields.many2one('wh.move', string=u'移库单'),
        'type': fields.selection(MOVE_LINE_TYPE, u'类型'),
        'state': fields.selection(MOVE_LINE_STATE, u'状态'),
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
        'subtotal': fields.float(u'金额', digits_compute=dp.get_precision('Accounting')),
        # 'subtotal': fields.function(_get_subtotal, type='float', string=u'金额',
        #     digits_compute=dp.get_precision('Accounting'), store={
        #         'wh.move.line': (lambda self, cr, uid, ids, ctx=None: ids, ['price', 'goods_qty'], 10),
        #     }),
        'note': fields.text(u'备注'),
    }

    _defaults = {
        'type': lambda self, cr, uid, ctx=None: ctx.get('type'),
        'warehouse_id': _get_default_warehouse,
        'warehouse_dest_id': _get_default_warehouse_dest,
    }
