# -*- coding: utf-8 -*-

from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from utils import safe_division
from openerp import models, fields, api


class wh_move_matching(models.Model):
    _name = 'wh.move.matching'

    line_in_id = fields.Many2one('wh.move.line', u'出库', ondelete='set null', required=True, index=True)
    line_out_id = fields.Many2one('wh.move.line', u'入库', ondelete='set null', required=True, index=True)
    qty = fields.Float(u'数量', digits_compute=dp.get_precision('Goods Quantity'), required=True)

    @api.model
    def create_matching(self, line_in_id, line_out_id, qty):
        res = {
            'line_out_id': line_out_id,
            'line_in_id': line_in_id,
            'qty': qty,
        }

        return self.create(res)


class wh_move_line(models.Model):
    _inherit = 'wh.move.line'

    qty_remaining = fields.Float(compute='_get_qty_remaining', string=u'剩余数量',
        digits_compute=dp.get_precision('Goods Quantity'), index=True, store=True)

    matching_in_ids = fields.One2many('wh.move.matching', 'line_in_id', string=u'关联的入库')
    matching_out_ids = fields.One2many('wh.move.matching', 'line_out_id', string=u'关联的出库')

    @api.multi
    def copy_data(self):
        res = super(wh_move_line, self).copy_data()

        if res.get('warehouse_id') and res.get('warehouse_dest_id'):
            vals = self.pool.get('warehouse').read([res.get('warehouse_id'),
                res.get('warehouse_dest_id')], ['type'])

            if vals[0].get('type') == 'stock' and vals[1].get('type') != 'stock':
                res.update({'price': 0, 'subtotal': 0})

        return res

    # 这样的function字段的使用方式需要验证一下
    @api.one
    @api.depends('goods_qty', 'warehouse_id', 'matching_in_ids', 'matching_out_ids')
    def _get_qty_remaining(self):
        self.qty_remaining = self.goods_qty - sum(match.qty for match in
            self.env['wh.move.matching'].search([('line_in_id', '=', self.id)]))

    @api.multi
    def get_matching_records_by_lot(self):
        for line in self:
            return [{'line_in_id': line.lot_id.id, 'qty': line.goods_qty}], \
                line.lot_id.price * line.goods_qty

        return []

    @api.multi
    def prev_action_done(self):
        matching_obj = self.env['wh.move.matching']
        for line in self:
            if line.warehouse_id.type == 'stock' and line.goods_id.is_using_matching():
                if line.goods_id.is_using_batch():
                    matching_records, subtotal = line.get_matching_records_by_lot()
                    for matching in matching_records:
                        matching_obj.create_matching(matching.get('line_in_id'),
                            line.id, matching.get('qty'))
                else:
                    matching_records, subtotal = line.goods_id.get_matching_records(
                        line.warehouse_id.id, line.goods_qty)

                    for matching in matching_records:
                        matching_obj.create_matching(matching.get('line_in_id'),
                            line.id, matching.get('qty'))

                line.price = safe_division(subtotal, line.goods_qty)
                line.subtotal = subtotal

        return super(wh_move_line, self).prev_action_done()

    @api.multi
    def prev_action_cancel(self):
        for line in self:
            if line.qty_remaining != line.goods_qty:
                raise osv.except_osv(u'错误', u'当前的入库已经被其他出库匹配，请先取消相关的出库')

            line.matching_in_ids.unlink()
            line.matching_out_ids.unlink()

        return super(wh_move_line, self).prev_action_cancel()
