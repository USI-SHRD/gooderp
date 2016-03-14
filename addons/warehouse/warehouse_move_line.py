# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp
from utils import safe_division
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('openerp.addons.warehouse', 'html'), autoescape=True)


class wh_move_line(osv.osv):
    _name = 'wh.move.line'

    MOVE_LINE_TYPE = [
        ('out', u'出库'),
        ('in', u'入库'),
    ]

    MOVE_LINE_STATE = [
        ('draft', u'草稿'),
        ('done', u'已审核'),
    ]

    def default_get(self, cr, uid, fields, context=None):
        res = super(wh_move_line, self).default_get(cr, uid, fields, context=context)
        context = context or {}
        if context.get('goods_id') and context.get('warehouse_id'):
            res.update({
                'goods_id': context.get('goods_id'),
                'warehouse_id': context.get('warehouse_id')
            })

        return res

    def get_real_price(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            return safe_division(line.subtotal, line.goods_qty)

    def name_get(self, cr, uid, ids, context=None):
        context = context or {}
        res = []
        for line in self.browse(cr, uid, ids, context=context):
            if context.get('lot'):
                res.append((line.id, '%s-%s' % (line.lot, line.qty_remaining)))
            else:
                res.append((line.id, '%s-%s->%s(%s, %s%s)' %
                    (line.move_id.name, line.warehouse_id.name, line.warehouse_dest_id.name,
                        line.goods_id.name, str(line.goods_qty), line.uom_id.name)))
        return res

    def check_availability(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.warehouse_dest_id.id == line.warehouse_id.id:
                raise osv.except_osv(u'错误', u'调出仓库不可以和调入仓库一样')

        return True

    def prev_action_done(self, cr, uid, ids, context=None):
        pass

    def action_done(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            line.check_availability()
            line.prev_action_done()
            line.write({
                'state': 'done',
                'date': fields.datetime.now(cr, uid),
            })

    def check_cancel(self, cr, uid, ids, context=None):
        pass

    def prev_action_cancel(self, cr, uid, ids, context=None):
        pass

    def action_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            line.check_cancel()
            line.prev_action_cancel()
            line.write({
                'state': 'draft',
                'date': False,
            })

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

    def onchange_price_by_out(self, cr, uid, ids, goods_id, warehouse_id, goods_qty, context=None):
        if goods_id and warehouse_id and goods_qty:
            subtotal, price = self.pool.get('goods').get_suggested_cost_by_warehouse(
                cr, uid, goods_id, warehouse_id, goods_qty, context=context)

            return {'value': {
                'price': price,
                'subtotal': subtotal,
            }}

        return {}

    def onchange_price_by_in(self, cr, uid, ids, goods_qty, price, context=None):
        if goods_qty and price:
            return {'value': {'subtotal': self._get_subtotal_util(
                cr, uid, goods_qty, price, context=context)}}

        return {'value': {'subtotal': 0}}

    def onchange_goods_by_in(self, cr, uid, ids, goods_id, goods_qty, context=None):
        # TODO 需要计算保质期
        if goods_id:
            goods = self.pool.get('goods').browse(cr, uid, goods_id, context=context)
            return {'value': {
                'uom_id': goods.uom_id.id,
                'using_batch': goods.using_batch,
                'force_batch_one': goods.force_batch_one,
                'goods_qty': goods.force_batch_one and 1 or goods_qty,
            }}

        return {}

    def onchange_lot_out(self, cr, uid, ids, lot_id, context=None):
        if lot_id:
            lot = self.browse(cr, uid, lot_id, context=context)
            return {'value': {'warehouse_id': lot.warehouse_dest_id.id,
                'goods_qty': lot.qty_remaining, 'lot_qty': lot.qty_remaining}}

        return {}

    def onchange_goods_by_out(self, cr, uid, ids, goods_id, warehouse_id, lot_id, goods_qty, compute_price=True, context=None):
        res = {}
        lot_domain = [('goods_id', '=', goods_id), ('state', '=', 'done'), ('lot', '!=', False), ('qty_remaining', '>', 0)]

        if goods_id:
            goods = self.pool.get('goods').browse(cr, uid, goods_id, context=context)
            res.update({
                'uom_id': goods.uom_id.id,
                'using_batch': goods.using_batch,
                'force_batch_one': goods.force_batch_one,
            })

            if warehouse_id:
                if compute_price and goods_qty:
                    subtotal, price = self.pool.get('goods').get_suggested_cost_by_warehouse(
                        cr, uid, goods_id, warehouse_id, goods_qty, context=context)

                    res.update({
                            'price': price,
                            'subtotal': subtotal,
                        })

                lot_domain.append(('warehouse_dest_id', '=', warehouse_id))

        if lot_id:
            lot = self.browse(cr, uid, lot_id, context=context)
            if warehouse_id and lot.warehouse_dest_id.id != warehouse_id:
                res.update({'lot_id': False})

            if goods_id and lot.goods_id.id != goods_id:
                res.update({'lot_id': False})

        return {'value': res, 'domain': {'lot_id': lot_domain}}

    def onchange_goods_by_internal(self, cr, uid, ids, goods_id, goods_qty, context=None):
        return self.onchange_goods_by_in(cr, uid, ids, goods_id, goods_qty, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.state == 'done':
                raise osv.except_osv(u'错误', u'不可以删除已经完成的明细')

        return super(wh_move_line, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'move_id': fields.many2one('wh.move', string=u'移库单', ondelete='cascade'),
        'date': fields.datetime(u'完成日期', copy=False),
        'type': fields.selection(MOVE_LINE_TYPE, u'类型'),
        'state': fields.selection(MOVE_LINE_STATE, u'状态', copy=False),
        'goods_id': fields.many2one('goods', string=u'产品', required=True, index=True),
        'using_batch': fields.related('goods_id', 'using_batch', type='boolean', string=u'批次管理'),
        'force_batch_one': fields.related('goods_id', 'force_batch_one', type='boolean', string=u'每批次数量为1'),
        'lot': fields.char(u'序列号'),
        'lot_id': fields.many2one('wh.move.line', u'序列号'),
        'lot_qty': fields.related('lot_id', 'qty_remaining', type='float', string=u'序列号数量'),
        'production_date': fields.date(u'生产日期'),
        'shelf_life': fields.integer(u'保质期(天)'),
        'valid_date': fields.date(u'有效期至'),
        'uom_id': fields.many2one('uom', string=u'单位'),
        'warehouse_id': fields.many2one('warehouse', string=u'调出仓库', required=True),
        'warehouse_dest_id': fields.many2one('warehouse', string=u'调入仓库', required=True),
        'goods_qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity')),
        'price': fields.float(u'单价', digits_compute=dp.get_precision('Accounting')),
        'subtotal': fields.float(u'金额', digits_compute=dp.get_precision('Accounting')),
        'note': fields.text(u'备注'),
    }

    _defaults = {
        'type': lambda self, cr, uid, ctx=None: ctx.get('type'),
        'goods_qty': lambda self, cr, uid, ctx=None: 1,
        'state': 'draft',
        'production_date': fields.date.context_today,
        'warehouse_id': _get_default_warehouse,
        'warehouse_dest_id': _get_default_warehouse_dest,
    }
