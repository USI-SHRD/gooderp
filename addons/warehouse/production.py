# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
from utils import inherits, inherits_after, create_name, safe_division
import openerp.addons.decimal_precision as dp
from itertools import islice


class wh_assembly(osv.osv):
    _name = 'wh.assembly'

    _inherits = {
        'wh.move': 'move_id',
    }

    def apportion_cost(self, cr, uid, ids, subtotal, context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            if not assembly.line_in_ids:
                continue

            collects = []
            for parent in assembly.line_in_ids:
                collects.append((parent, parent.goods_id.get_suggested_cost_by_warehouse(
                    parent.warehouse_dest_id.id, parent.goods_qty)[0]))

            amount_total, collect_parent_subtotal = sum(collect[1] for collect in collects), 0
            for parent, amount in islice(collects, 0, len(collects) - 1):
                parent_subtotal = safe_division(amount, amount_total) * subtotal
                collect_parent_subtotal += parent_subtotal
                parent.write({
                        'price': safe_division(parent_subtotal, parent.goods_qty),
                        'subtotal': parent_subtotal,
                    })

            # 最后一行数据使用总金额减去已经消耗的金额来计算
            last_parent_subtotal = subtotal - collect_parent_subtotal
            collects[-1][0].write({
                    'price': safe_division(last_parent_subtotal, collects[-1][0].goods_qty),
                    'subtotal': last_parent_subtotal,
                })

        return True

    def update_parent_price(self, cr, uid, ids, context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            subtotal = sum(child.subtotal for child in assembly.line_out_ids) + assembly.fee

            assembly.apportion_cost(subtotal)
        return True

    def check_parent_length(self, cr, uid, ids, context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            if not len(assembly.line_in_ids) or not len(assembly.line_out_ids):
                raise osv.except_osv(u'错误', u'组合件和子件的产品必须存在')

        return True

    @inherits_after(res_back=False)
    def approve_order(self, cr, uid, ids, context=None):
        self.check_parent_length(cr, uid, ids, context=context)
        return self.update_parent_price(cr, uid, ids, context=context)

    @inherits()
    def cancel_approved_order(self, cr, uid, ids, context=None):
        return True

    @inherits_after()
    def unlink(self, cr, uid, ids, context=None):
        return super(wh_assembly, self).unlink(cr, uid, ids, context=context)

    @create_name
    def create(self, cr, uid, vals, context=None):
        res_id = super(wh_assembly, self).create(cr, uid, vals, context=context)
        self.update_parent_price(cr, uid, res_id, context=context)

        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(wh_assembly, self).write(cr, uid, ids, vals, context=context)
        self.update_parent_price(cr, uid, ids, context=context)

        return res

    def onchange_bom(self, cr, uid, ids, bom_id, context=None):
        line_out_ids, line_in_ids = [], []

        # TODO
        warehouse_id = self.pool.get('warehouse').search(cr, uid, [('type', '=', 'stock')], limit=1, context=context)[0]
        if bom_id:
            bom = self.pool.get('wh.bom').browse(cr, uid, bom_id, context=context)
            line_in_ids = [{
                'goods_id': line.goods_id.id,
                'warehouse_id': self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'production'),
                'warehouse_dest_id': warehouse_id,
                'uom_id': line.goods_id.uom_id.id,
                'goods_qty': line.goods_qty,
            } for line in bom.line_parent_ids]

            line_out_ids = []
            for line in bom.line_child_ids:
                subtotal, price = self.pool.get('goods').get_suggested_cost_by_warehouse(
                    cr, uid, line.goods_id.id, warehouse_id, line.goods_qty, context=context)

                line_out_ids.append({
                        'goods_id': line.goods_id.id,
                        'warehouse_id': warehouse_id,
                        'warehouse_dest_id': self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'production'),
                        'uom_id': line.goods_id.uom_id.id,
                        'goods_qty': line.goods_qty,
                        'price': price,
                        'subtotal': subtotal,
                    })

        return {'value': {'line_out_ids': line_out_ids, 'line_in_ids': line_in_ids}}

    def update_bom(self, cr, uid, ids, context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            if assembly.bom_id:
                return assembly.save_bom()
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'save.bom.memory',
                    'view_mode': 'form',
                    'target': 'new',
                }

    def save_bom(self, cr, uid, ids, name='', context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            line_parent_ids = [[0, False, {
                'goods_id': line.goods_id.id,
                'goods_qty': line.goods_qty,
            }] for line in assembly.line_in_ids]

            line_child_ids = [[0, False, {
                'goods_id': line.goods_id.id,
                'goods_qty': line.goods_qty,
            }] for line in assembly.line_out_ids]

            if assembly.bom_id:
                assembly.bom_id.line_parent_ids.unlink()
                assembly.bom_id.line_child_ids.unlink()

                assembly.bom_id.write({'line_parent_ids': line_parent_ids, 'line_child_ids': line_child_ids})
            else:
                bom_id = self.pool.get('wh.bom').create(cr, uid, {
                        'name': name,
                        'type': 'assembly',
                        'line_parent_ids': line_parent_ids,
                        'line_child_ids': line_child_ids,
                    }, context=context)
                assembly.write({'bom_id': bom_id})

        return True

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'bom_id': fields.many2one('wh.bom', u'模板', domain=[('type', '=', 'assembly')], context={'type': 'assembly'}),
        'fee': fields.float(u'组装费用', digits_compute=dp.get_precision('Accounting')),
    }


class wh_disassembly(osv.osv):
    _name = 'wh.disassembly'

    _inherits = {
        'wh.move': 'move_id',
    }

    def apportion_cost(self, cr, uid, ids, subtotal, context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            if not assembly.line_in_ids:
                continue

            collects = []
            for child in assembly.line_in_ids:
                collects.append((child, child.goods_id.get_suggested_cost_by_warehouse(
                    child.warehouse_dest_id.id, child.goods_qty)[0]))

            amount_total, collect_child_subtotal = sum(collect[1] for collect in collects), 0
            for child, amount in islice(collects, 0, len(collects) - 1):
                child_subtotal = safe_division(amount, amount_total) * subtotal
                collect_child_subtotal += child_subtotal
                child.write({
                        'price': safe_division(child_subtotal, child.goods_qty),
                        'subtotal': child_subtotal,
                    })

            # 最后一行数据使用总金额减去已经消耗的金额来计算
            last_child_subtotal = subtotal - collect_child_subtotal
            collects[-1][0].write({
                    'price': safe_division(last_child_subtotal, collects[-1][0].goods_qty),
                    'subtotal': last_child_subtotal,
                })

        return True

    def update_child_price(self, cr, uid, ids, context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            subtotal = sum(child.subtotal for child in assembly.line_out_ids) + assembly.fee

            assembly.apportion_cost(subtotal)
        return True

    def check_parent_length(self, cr, uid, ids, context=None):
        for assembly in self.browse(cr, uid, ids, context=context):
            if not len(assembly.line_in_ids) or not len(assembly.line_out_ids):
                raise osv.except_osv(u'错误', u'组合件和子件的产品必须存在')

        return True

    @inherits_after(res_back=False)
    def approve_order(self, cr, uid, ids, context=None):
        self.check_parent_length(cr, uid, ids, context=context)
        return self.update_child_price(cr, uid, ids, context=context)

    @inherits()
    def cancel_approved_order(self, cr, uid, ids, context=None):
        return True

    @inherits_after()
    def unlink(self, cr, uid, ids, context=None):
        return super(wh_disassembly, self).unlink(cr, uid, ids, context=context)

    @create_name
    def create(self, cr, uid, vals, context=None):
        res_id = super(wh_disassembly, self).create(cr, uid, vals, context=context)
        self.update_child_price(cr, uid, res_id, context=context)

        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(wh_disassembly, self).write(cr, uid, ids, vals, context=context)
        self.update_child_price(cr, uid, ids, context=context)

        return res

    def onchange_bom(self, cr, uid, ids, bom_id, context=None):
        line_out_ids, line_in_ids = [], []
        # TODO
        warehouse_id = self.pool.get('warehouse').search(cr, uid, [('type', '=', 'stock')], limit=1, context=context)[0]
        if bom_id:
            bom = self.pool.get('wh.bom').browse(cr, uid, bom_id, context=context)
            line_out_ids = []
            for line in bom.line_parent_ids:
                subtotal, price = self.pool.get('goods').get_suggested_cost_by_warehouse(
                    cr, uid, line.goods_id.id, warehouse_id, line.goods_qty, context=context)
                line_out_ids.append({
                        'goods_id': line.goods_id.id,
                        'warehouse_id': self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'production'),
                        'warehouse_dest_id': warehouse_id,
                        'uom_id': line.goods_id.uom_id.id,
                        'goods_qty': line.goods_qty,
                        'price': price,
                        'subtotal': subtotal,
                    })

            line_in_ids = [{
                'goods_id': line.goods_id.id,
                'warehouse_id': warehouse_id,
                'warehouse_dest_id': self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'production'),
                'uom_id': line.goods_id.uom_id.id,
                'goods_qty': line.goods_qty,
            } for line in bom.line_child_ids]

        return {'value': {'line_out_ids': line_out_ids, 'line_in_ids': line_in_ids}}

    def update_bom(self, cr, uid, ids, context=None):
        for disassembly in self.browse(cr, uid, ids, context=context):
            if disassembly.bom_id:
                return disassembly.save_bom()
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'save.bom.memory',
                    'view_mode': 'form',
                    'target': 'new',
                }

    def save_bom(self, cr, uid, ids, name='', context=None):
        for disassembly in self.browse(cr, uid, ids, context=context):
            line_child_ids = [[0, False, {
                'goods_id': line.goods_id.id,
                'goods_qty': line.goods_qty,
            }] for line in disassembly.line_in_ids]

            line_parent_ids = [[0, False, {
                'goods_id': line.goods_id.id,
                'goods_qty': line.goods_qty,
            }] for line in disassembly.line_out_ids]

            if disassembly.bom_id:
                disassembly.bom_id.line_parent_ids.unlink()
                disassembly.bom_id.line_child_ids.unlink()

                disassembly.bom_id.write({'line_parent_ids': line_parent_ids, 'line_child_ids': line_child_ids})
            else:
                bom_id = self.pool.get('wh.bom').create(cr, uid, {
                        'name': name,
                        'type': 'disassembly',
                        'line_parent_ids': line_parent_ids,
                        'line_child_ids': line_child_ids,
                    }, context=context)
                disassembly.write({'bom_id': bom_id})

        return True

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'bom_id': fields.many2one('wh.bom', u'模板', domain=[('type', '=', 'disassembly')], context={'type': 'disassembly'}),
        # 'is_apportion': fields.boolean(u'分摊分析'),
        'fee': fields.float(u'拆卸费用', digits_compute=dp.get_precision('Accounting')),
    }


class wh_bom(osv.osv):
    _name = 'wh.bom'

    BOM_TYPE = [
        ('assembly', u'组装单'),
        ('disassembly', u'拆卸单'),
    ]

    _columns = {
        'name': fields.char(u'模板名称'),
        'type': fields.selection(BOM_TYPE, u'类型'),
        'line_parent_ids': fields.one2many('wh.bom.line', 'bom_id', u'组合件', domain=[('type', '=', 'parent')], context={'type': 'parent'}, copy=True),
        'line_child_ids': fields.one2many('wh.bom.line', 'bom_id', u'子件', domain=[('type', '=', 'child')], context={'type': 'child'}, copy=True),
    }

    _defaults = {
        'type': lambda self, cr, uid, ctx=None: ctx.get('type'),
    }


class wh_bom_line(osv.osv):
    _name = 'wh.bom.line'

    BOM_LINE_TYPE = [
        ('parent', u'组合件'),
        ('child', u'子间'),
    ]

    _columns = {
        'bom_id': fields.many2one('wh.bom', u'模板'),
        'type': fields.selection(BOM_LINE_TYPE, u'类型'),
        'goods_id': fields.many2one('goods', u'产品'),
        'goods_qty': fields.float(u'数量', digits_compute=dp.get_precision('Goods Quantity')),
    }

    _defaults = {
        'type': lambda self, cr, uid, ctx=None: ctx.get('type'),
        'goods_id': 1,
    }
