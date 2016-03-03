# -*- coding: utf-8 -*-

from openerp.osv import osv


class goods(osv.osv):
    _inherit = 'goods'

    # 使用SQL来取得指定产品情况下的库存数量
    def get_stock_qty(self, cr, uid, ids, context=None):
        if isinstance(ids, (long, int)):
            ids = [ids]

        cr.execute('''
            SELECT sum(line.qty_remaining) as qty,
                   sum(line.qty_remaining * (line.subtotal / line.goods_qty)) as subtotal,
                   wh.name as warehouse
            FROM wh_move_line line
            LEFT JOIN warehouse wh ON line.warehouse_dest_id = wh.id

            WHERE line.qty_remaining > 0
              AND wh.type = 'stock'
              AND line.state = 'done'
              AND line.goods_id = %s

            GROUP BY wh.name
        ''' % (ids[0], ))

        return cr.dictfetchall()

    def get_suggested_cost_by_warehouse(self, cr, uid, ids, warehouse_id, qty, context=None):
        records, subtotal = self.get_matching_records(cr, uid,
            ids, warehouse_id, qty, ignore_stock=True, context=context)

        return subtotal, sum(record.get('qty') for record in records)

    def is_using_matching(self, cr, uid, ids, context=None):
        return True

    def get_matching_records(self, cr, uid, ids, warehouse_id, qty, ignore_stock=False, context=None):
        line_obj = self.pool.get('wh.move.line')
        matching_records = []
        for goods in self.browse(cr, uid, ids, context=context):
            domain = [
                ('qty_remaining', '>', 0),
                ('state', '=', 'done'),
                ('warehouse_dest_id', '=', warehouse_id),
                ('goods_id', '=', goods.id)
            ]

            # TODO @zzx需要在大量数据的情况下评估一下速度
            line_ids = line_obj.search(cr, uid, domain, order='date, id', context=context)
            qty_to_go, subtotal = qty, 0
            for line in line_obj.browse(cr, uid, line_ids, context=context):
                if qty_to_go <= 0:
                    break

                matching_qty = min(line.qty_remaining, qty_to_go)
                matching_records.append({'line_in_id': line.id, 'qty': matching_qty})
                subtotal += matching_qty * line.get_real_price()

                qty_to_go -= matching_qty
            else:
                if not ignore_stock and qty_to_go > 0:
                    raise osv.except_osv(u'错误', u'产品%s的库存数量不够本次出库行为' % (goods.name, ))

            return matching_records, subtotal
