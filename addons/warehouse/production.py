# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
from utils import inherits, inherits_after, create_name
import openerp.addons.decimal_precision as dp


class wh_assembly(osv.osv):
    _name = 'wh.assembly'

    _inherits = {
        'wh.move': 'move_id',
    }

    @inherits()
    def approve_order(self, cr, uid, ids, context=None):
        return True

    @inherits()
    def cancel_approved_order(self, cr, uid, ids, context=None):
        return True

    @inherits_after()
    def unlink(self, cr, uid, ids, context=None):
        return super(wh_assembly, self).unlink(cr, uid, ids, context=context)

    @create_name
    def create(self, cr, uid, vals, context=None):
        return super(wh_assembly, self).create(cr, uid, vals, context=context)

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
                'price': 0,
            } for line in bom.line_parent_ids]

            line_out_ids = [{
                'goods_id': line.goods_id.id,
                'warehouse_id': warehouse_id,
                'warehouse_dest_id': self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'production'),
                'uom_id': line.goods_id.uom_id.id,
                'goods_qty': line.goods_qty,
                'price': 0,
            } for line in bom.line_child_ids]

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

    @inherits()
    def approve_order(self, cr, uid, ids, context=None):
        return True

    @inherits()
    def cancel_approved_order(self, cr, uid, ids, context=None):
        return True

    @inherits_after()
    def unlink(self, cr, uid, ids, context=None):
        return super(wh_disassembly, self).unlink(cr, uid, ids, context=context)

    @create_name
    def create(self, cr, uid, vals, context=None):
        return super(wh_disassembly, self).create(cr, uid, vals, context=context)

    def onchange_bom(self, cr, uid, ids, bom_id, context=None):
        line_out_ids, line_in_ids = [], []
        # TODO
        warehouse_id = self.pool.get('warehouse').search(cr, uid, [('type', '=', 'stock')], limit=1, context=context)[0]
        if bom_id:
            bom = self.pool.get('wh.bom').browse(cr, uid, bom_id, context=context)
            line_out_ids = [{
                'goods_id': line.goods_id.id,
                'warehouse_id': self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'production'),
                'warehouse_dest_id': warehouse_id,
                'uom_id': line.goods_id.uom_id.id,
                'goods_qty': line.goods_qty,
                'price': 0,
            } for line in bom.line_parent_ids]

            line_in_ids = [{
                'goods_id': line.goods_id.id,
                'warehouse_id': warehouse_id,
                'warehouse_dest_id': self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'production'),
                'uom_id': line.goods_id.uom_id.id,
                'goods_qty': line.goods_qty,
                'price': 0,
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
