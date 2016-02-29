# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class warehouse(osv.osv):
    _inherit = 'warehouse'

    WAREHOUSE_TYPE = [
        ('stock', u'库存'),
        ('supplier', u'供应商'),
        ('customer', u'客户'),
        ('inventory', u'盘点'),
        ('production', u'生产'),
        ('others', u'其他'),
    ]

    # 使用SQL来取得指定仓库情况下的库存数量
    def get_stock_qty(self, cr, uid, ids, context=None):
        if isinstance(ids, (long, int)):
            ids = [ids]

        cr.execute('''
            SELECT sum(line.qty_remaining) as qty,
                   sum(line.qty_remaining * (line.subtotal / line.goods_qty)) as subtotal,
                   goods.name as goods
            FROM wh_move_line line
            LEFT JOIN warehouse wh ON line.warehouse_dest_id = wh.id
            LEFT JOIN goods goods ON line.goods_id = goods.id

            WHERE line.qty_remaining > 0
              AND wh.type = 'stock'
              AND line.state = 'done'
              AND line.warehouse_dest_id = %s

            GROUP BY wh.name, goods.name
        ''' % (ids[0], ))

        return cr.dictfetchall()

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        args = args or []
        if not filter(lambda _type: _type[0] == 'type', args):
            args = [['type', '=', 'stock']] + args

        return super(warehouse, self).name_search(cr, user, name,
            args=args, operator=operator, context=context, limit=limit)

    def get_warehouse_by_type(self, cr, uid, _type, context=None):
        if not _type or _type not in map(lambda _type: _type[0], self.WAREHOUSE_TYPE):
            raise ValueError(u'错误，仓库类型"%s"不在预先定义的type之中，请联系管理员' % _type)

        warehouse_ids = self.search(cr, uid, [('type', '=', _type)], limit=1, order='id asc', context=context)
        if not warehouse_ids:
            raise osv.except_osv(u'错误', u'不存在该类型"%s"的仓库，请检查基础数据是否全部导入')

        return warehouse_ids[0]

    _columns = {
        'name': fields.char(u'仓库名称'),
        'code': fields.char(u'仓库编号'),
        'type': fields.selection(WAREHOUSE_TYPE, '类型'),
        'active': fields.boolean(u'有效'),
    }

    _defaults = {
        'active': True,
        'type': 'stock',
    }
