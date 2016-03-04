# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.fields import fields
import openerp.addons.decimal_precision as dp
from utils import safe_division


class wh_move_matching(osv.osv):
    _name = 'wh.move.matching'

    def create_matching(self, cr, uid, line_in_id, line_out_id, qty, context=None):
        return self.create(cr, uid, {
                'line_in_id': line_in_id,
                'line_out_id': line_out_id,
                'qty': qty,
            }, context=context)

    _columns = {
        'line_in_id': fields.many2one('wh.move.line', u'出库', ondelete='set null', required=True, index=True),
        'line_out_id': fields.many2one('wh.move.line', u'入库', ondelete='set null', required=True),
        'qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity'), required=True),
    }


class wh_move_line(osv.osv):
    _inherit = 'wh.move.line'

    def copy_data(self, cr, uid, ids, context=None):
        res = super(wh_move_line, self).copy_data(cr, uid, ids, context=context)

        if res.get('warehouse_id') and res.get('warehouse_dest_id'):
            vals = self.pool.get('warehouse').read(cr, uid, [res.get('warehouse_id'),
                res.get('warehouse_dest_id')], ['type'], context=context)

            if vals[0].get('type') == 'stock' and vals[1].get('type') != 'stock':
                res.update({'price': 0, 'subtotal': 0})

        return res

    def _get_moves_from_matchings(self, cr, uid, ids, context=None):
        return list(set(match.line_in_id.id for match in
            self.pool.get('wh.move.matching').browse(cr, uid, ids, context=context)))

    def _get_qty_remaining(self, cr, uid, ids, field_names, arg, context=None):
        match_obj = self.pool.get('wh.move.matching')
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            qty = line.goods_qty
            match_ids = match_obj.search(cr, uid, [('line_in_id', '=', line.id)], context=context)
            for match in match_obj.browse(cr, uid, match_ids, context=context):
                qty -= match.qty

            res.update({line.id: qty})

        return res

    def prev_action_done(self, cr, uid, ids, context=None):
        matching_obj = self.pool.get('wh.move.matching')
        for line in self.browse(cr, uid, ids, context=context):
            if line.warehouse_id.type == 'stock' and line.goods_id.is_using_matching():
                matching_records, subtotal = line.goods_id.get_matching_records(
                    line.warehouse_id.id, line.goods_qty, context=context)

                for matching in matching_records:
                    matching_obj.create_matching(cr, uid,
                        matching.get('line_in_id'), line.id, matching.get('qty'), context=context)

                line.write({'price': safe_division(subtotal, line.goods_qty), 'subtotal': subtotal})

        return super(wh_move_line, self).prev_action_done(cr, uid, ids, context=context)

    def prev_action_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.qty_remaining != line.goods_qty:
                raise osv.except_osv(u'错误', u'当前的入库已经被其他出库匹配，请先取消相关的出库')

            line.matching_in_ids.unlink()
            line.matching_out_ids.unlink()

        return super(wh_move_line, self).prev_action_cancel(cr, uid, ids, context=context)

    _columns = {
        'qty_remaining': fields.function(_get_qty_remaining, type='float', string='剩余数量',
            store={
                'wh.move.matching': (_get_moves_from_matchings, ['qty', 'move_in_id', 'move_out_id'], 10),
                'wh.move.line': (lambda self, cr, uid, ids, ctx: ids, ['goods_qty', 'warehouse_id'], 10)
            }, index=True),

        'matching_in_ids': fields.one2many('wh.move.matching', 'line_in_id'),
        'matching_out_ids': fields.one2many('wh.move.matching', 'line_out_id'),
    }
