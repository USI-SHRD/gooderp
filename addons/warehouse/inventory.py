# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class wh_inventory(osv.osv):
    _name = 'wh.inventory'

    INVENTORY_STATE = [
        ('draft', u'草稿'),
        ('query', u'查询中'),
        ('confirmed', u'待确认盘盈盘亏'),
        ('done', u'完成'),
    ]

    def requery_inventory(self, cr, uid, ids, context=None):
        self.delete_confirmed_wh(cr, uid, ids, context=context)
        return self.write(cr, uid, ids, {'state': 'query'}, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            if inventory.state == 'done':
                raise osv.except_osv(u'错误', u'不可以删除一个完成的单据')

            inventory.delete_confirmed_wh()

        return super(wh_inventory, self).unlink(cr, uid, ids, context=context)

    def delete_confirmed_wh(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            if inventory.state == 'confirmed':
                if (inventory.out_id and inventory.out_id.state == 'done') or (inventory.in_id and inventory.in_id.state == 'done'):
                    raise osv.except_osv(u'错误', u'请先反审核掉相关的盘盈盘亏单据')
                else:
                    inventory.out_id.unlink()
                    inventory.in_id.unlink()

        return True

    def check_done(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            if inventory.state == 'confirmed' and \
                (not inventory.out_id or inventory.out_id.state == 'done') and \
                    (not inventory.in_id or inventory.in_id.state == 'done'):
                return inventory.write({'state': 'done'})

        return False

    def open_out(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'wh.out',
                'view_mode': 'form',
                'res_id': inventory.out_id.id,
            }

    def open_in(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'wh.in',
                'view_mode': 'form',
                'res_id': inventory.in_id.id,
            }

    def delete_line(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            inventory.line_ids.unlink(context=context)

        return True

    def create_losses_out(self, cr, uid, inventory, out_line, context=None):
        context_out = dict(context or {}, warehouse_dest_type='inventory')

        out_vals = {
            'type': 'losses',
            'line_out_ids': [],
        }

        for line in out_line:
            out_vals['line_out_ids'].append([0, False, line.get_move_line(context=context_out)])

        out_id = self.pool.get('wh.out').create(cr, uid, out_vals, context=context_out)
        inventory.write({'out_id': out_id})

    def create_overage_in(self, cr, uid, inventory, in_line, context=None):
        context_in = dict(context or {}, warehouse_type='inventory')

        in_vals = {
            'type': 'overage',
            'line_in_ids': [],
        }

        for line in in_line:
            in_vals['line_in_ids'].append([0, False, line.get_move_line(context=context_in)])

        in_id = self.pool.get('wh.in').create(cr, uid, in_vals, context=context_in)
        inventory.write({'in_id': in_id})

    def generate_inventory(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            out_line, in_line = [], []
            for line in (line for line in inventory.line_ids if line.difference_qty):
                if line.difference_qty < 0:
                    out_line.append(line)
                else:
                    in_line.append(line)

            if out_line:
                self.create_losses_out(cr, uid, inventory, out_line, context=context)

            if in_line:
                self.create_overage_in(cr, uid, inventory, in_line, context=context)

            if out_line or in_line:
                inventory.write({'state': 'confirmed'})

        return True

    def get_line_detail(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        inventory = self.browse(cr, uid, ids, context=context)
        sql_text = '''
            SELECT wh.id as warehouse_id,
                   goods.id as goods_id,
                   uom.id as uom_id,
                   sum(line.qty_remaining) as qty

            FROM wh_move_line line
            LEFT JOIN goods goods ON line.goods_id = goods.id
                LEFT JOIN uom uom ON goods.uom_id = uom.id
            LEFT JOIN warehouse wh ON line.warehouse_dest_id = wh.id

            WHERE line.qty_remaining > 0
              AND wh.type = 'stock'
              AND line.state = 'done'
              %s

            GROUP BY wh.id, goods.id, uom.id
        '''

        extra_text = ''
        # TODO @zzx 可能需要添加一种全部仓库的判断
        if inventory.warehouse_id:
            extra_text += ' AND wh.id = %s' % inventory.warehouse_id.id

        if inventory.goods:
            extra_text += " AND goods.name ILIKE '%%%s%%' " % inventory.goods

        cr.execute(sql_text % extra_text)
        return cr.dictfetchall()

    def query_inventory(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('wh.inventory.line')
        for inventory in self.browse(cr, uid, ids, context=context):
            inventory.delete_line(context=context)
            line_ids = inventory.get_line_detail(context=context)

            for line in line_ids:
                line_obj.create(cr, uid, {
                        'inventory_id': inventory.id,
                        'warehouse_id': line.get('warehouse_id'),
                        'goods_id': line.get('goods_id'),
                        'uom_id': line.get('uom_id'),
                        'real_qty': line.get('qty'),
                    }, context=context)

            if line_ids:
                inventory.write({'state': 'query'})

        return True

    _columns = {
        'date': fields.date(u'日期'),
        'name': fields.char(u'名称', copy=False),
        'warehouse_id': fields.many2one('warehouse', u'仓库'),
        'goods': fields.char(u'产品'),
        'zero_inventory': fields.boolean(u'零库存'),
        'serial_numbe': fields.boolean(u'序列号产品'),
        'out_id': fields.many2one('wh.out', u'盘亏单据', copy=False),
        'in_id': fields.many2one('wh.in', u'盘盈单据', copy=False),
        'state': fields.selection(INVENTORY_STATE, u'状态', copy=False),
        'line_ids': fields.one2many('wh.inventory.line', 'inventory_id', u'明细', copy=False),
    }

    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
        'name': '/',
    }


class wh_inventory_line(osv.osv):
    _name = 'wh.inventory.line'

    def onchange_qty(self, cr, uid, ids, real_qty, inventory_qty, context=None):
        return {'value': {'difference_qty': inventory_qty - real_qty}}

    def get_move_line(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        line = self.browse(cr, uid, ids, context=context)

        inventory_warehouse = self.pool.get('warehouse').get_warehouse_by_type(cr, uid, 'inventory')
        return {
            'warehouse_id': line.difference_qty < 0 and line.warehouse_id.id or inventory_warehouse,
            'warehouse_dest_id': line.difference_qty > 0 and line.warehouse_id.id or inventory_warehouse,
            'goods_id': line.goods_id.id,
            'uom_id': line.uom_id.id,
            'goods_qty': abs(line.difference_qty)
        }

    _columns = {
        'inventory_id': fields.many2one('wh.inventory', u'盘点', ondelete='cascade'),
        'warehouse_id': fields.many2one('warehouse', u'仓库'),
        'goods_id': fields.many2one('goods', u'产品'),
        'uom_id': fields.many2one('uom', u'单位'),
        'real_qty': fields.float(u'系统库存', digits_compute=dp.get_precision('Goods Quantity')),
        'inventory_qty': fields.float(u'盘点库存', digits_compute=dp.get_precision('Goods Quantity')),
        'difference_qty': fields.float(u'盘盈盘亏', digits_compute=dp.get_precision('Goods Quantity')),
    }


class wh_out(osv.osv):
    _inherit = 'wh.out'

    _columns = {
        'inventory_ids': fields.one2many('wh.inventory', 'out_id', u'盘点单'),
    }

    def approve_order(self, cr, uid, ids, context=None):
        res = super(wh_out, self).approve_order(cr, uid, ids, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            move.inventory_ids.check_done()

        return res


class wh_in(osv.osv):
    _inherit = 'wh.in'

    _columns = {
        'inventory_ids': fields.one2many('wh.inventory', 'in_id', u'盘点单'),
    }

    def approve_order(self, cr, uid, ids, context=None):
        res = super(wh_in, self).approve_order(cr, uid, ids, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            move.inventory_ids.check_done()

        return res
