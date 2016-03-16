# -*- coding: utf-8 -*-

# from openerp import tools
from openerp.osv import fields
from openerp.osv import osv
import openerp.addons.decimal_precision as dp


class report_stock_transceive(osv.osv):
    _name = 'report.stock.transceive'
    _auto = False

    _columns = {
        'goods': fields.char(u'产品'),
        'uom': fields.char(u'单位'),
        'warehouse': fields.char(u'仓库'),
        'goods_qty_begain': fields.float('期初数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_begain': fields.float(u'期初成本', digits_compute=dp.get_precision('Accounting')),
        'goods_qty_end': fields.float('期末数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_end': fields.float(u'期末成本', digits_compute=dp.get_precision('Accounting')),
        'goods_qty_out': fields.float('出库数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_out': fields.float(u'出库成本', digits_compute=dp.get_precision('Accounting')),
        'goods_qty_in': fields.float('入库数量', digits_compute=dp.get_precision('Goods Quantity')),
        'cost_in': fields.float(u'入库成本', digits_compute=dp.get_precision('Accounting')),
    }

    def select_sql(self, sql_type='out'):
        return '''
        SELECT min(line.id) as id,
               goods.name as goods,
               uom.name as uom,
               wh.name as warehouse,
               sum(case when line.date < '{date_start}' THEN line.goods_qty ELSE 0 END) as goods_qty_begain,
               sum(case when line.date < '{date_start}' THEN line.subtotal ELSE 0 END) as cost_begain,
               sum(case when line.date < '{date_end}' THEN line.goods_qty ELSE 0 END) as goods_qty_end,
               sum(case when line.date < '{date_end}' THEN line.subtotal ELSE 0 END) as cost_end,
               sum(case when line.date < '{date_end}' AND line.date >= '{date_start}' THEN line.goods_qty ELSE 0 END) as goods_qty,
               sum(case when line.date < '{date_end}' AND line.date >= '{date_start}' THEN line.subtotal ELSE 0 END) as cost
        '''

    def from_sql(self, sql_type='out'):
        return '''
        FROM wh_move_line line
            LEFT JOIN goods goods ON line.goods_id = goods.id
                LEFT JOIN uom uom ON goods.uom_id = uom.id
            LEFT JOIN warehouse wh ON line.%s = wh.id
        ''' % (sql_type == 'out' and 'warehouse_id' or 'warehouse_dest_id')

    def where_sql(self, sql_type='out'):
        return '''
        WHERE line.state = 'done'
          AND wh.type = 'stock'
          AND line.date < '{date_end}'
          AND wh.name ilike '%{warehouse}%'
          AND goods.name ilike '%{goods}%'
        '''

    def group_sql(self, sql_type='out'):
        return '''
        GROUP BY goods.name, uom.name, wh.name
        '''

    def order_sql(self, sql_type='out'):
        return '''
        ORDER BY goods.name, wh.name
        '''

    def get_context(self, sql_type='out', context=None):
        return {
            'date_start': context.get('date_start') or '',
            'date_end': context.get('date_end') or '',
            'warehouse': context.get('warehouse') or '',
            'goods': context.get('goods') or '',
        }

    def collect_history_stock_by_sql(self, cr, sql_type='out', context=None):
        context = context or {}
        cr.execute((self.select_sql(sql_type) + self.from_sql(sql_type) + self.where_sql(
            sql_type) + self.group_sql(sql_type) + self.order_sql(
            sql_type)).format(**self.get_context(sql_type, context=context)))

        return cr.dictfetchall()

    def get_record_key(self, record, sql_type='out'):
        return (record.get('goods'), record.get('uom'), record.get('warehouse'))

    def unzip_record_key(self, key):
        return {
            'goods': key[0],
            'uom': key[1],
            'warehouse': key[2],
        }

    def get_record_value(self, record, sql_type='out'):
        return {
            'id': record.get('id'),
            'goods_qty_begain': 0,
            'cost_begain': 0,
            'goods_qty_end': 0,
            'cost_end': 0,
            'goods_qty_out': 0,
            'cost_out': 0,
            'goods_qty_in': 0,
            'cost_in': 0,
        }

    def update_record_value(self, value, record, sql_type='out'):
        tag = sql_type == 'out' and -1 or 1
        value.update({
                'goods_qty_begain': value.get('goods_qty_begain', 0) + tag * record.get('goods_qty_begain', 0),
                'cost_begain': value.get('cost_begain', 0) + tag * record.get('cost_begain', 0),
                'goods_qty_end': value.get('goods_qty_end', 0) + tag * record.get('goods_qty_end', 0),
                'cost_end': value.get('cost_end', 0) + tag * record.get('cost_end', 0),

                'goods_qty_out': value.get('goods_qty_out', 0) + (sql_type == 'out' and record.get('goods_qty', 0) or 0),
                'cost_out': value.get('cost_out', 0) + (sql_type == 'out' and record.get('cost', 0) or 0),
                'goods_qty_in': value.get('goods_qty_in', 0) + (sql_type == 'in' and record.get('goods_qty', 0) or 0),
                'cost_in': value.get('cost_in', 0) + (sql_type == 'in' and record.get('cost', 0) or 0),
            })

    def compute_history_stock_by_collect(self, res, records, sql_type='out'):
        for record in records:
            record_key = self.get_record_key(record, sql_type=sql_type)
            if not res.get(record_key):
                res[record_key] = self.get_record_value(record, sql_type=sql_type)

            self.update_record_value(res[record_key], record, sql_type=sql_type)

    def _compute_domain(self, result, domain):
        print '     domain = ', domain, type(domain)
        pass

    def _compute_order(self, result, order):
        # TODO 暂时不支持多重排序
        if order:
            order = order.partition(',')[0].partition(' ')
            result.sort(key=lambda item: item.get(order[0]), reverse=order[2] == 'ASC')

    def _compute_limit_and_offset(self, result, limit, offset):
        result = result[offset:limit + offset]

    def search_read(self, cr, uid, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        context = context or {}
        print '------------search_read-----------------'

        out_collection = self.collect_history_stock_by_sql(cr, sql_type='out', context=context)
        in_collection = self.collect_history_stock_by_sql(cr, sql_type='in', context=context)

        res = {}
        self.compute_history_stock_by_collect(res, in_collection, sql_type='in')
        self.compute_history_stock_by_collect(res, out_collection, sql_type='out')

        result = []
        for key, value in res.iteritems():
            value.update(self.unzip_record_key(key))
            result.append(value)

        self._compute_domain(result, domain)
        self._compute_order(result, order)
        self._compute_limit_and_offset(result, limit, offset)

        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
