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

    def check_valid_domain(self, domain):
        if not isinstance(domain, list):
            raise osv.except_osv(u'错误', u'不可识别的domain条件，请检查domain"%s"是否正确' % domain)

    def get_next_or_domain(self, domains, index):
        left_index, right_index, current_index = [index] * 3
        domain = domains[current_index]
        current_index += 1
        if domain == '|':
            _, current_index = self.get_next_or_domain(domains, current_index)
        else:
            self.check_valid_domain(domain)

        left_index = current_index

        domain = domains[current_index]
        current_index += 1
        if domain == '|':
            _, current_index = self.get_next_or_domain(domains, current_index)
        else:
            self.check_valid_domain(domain)

        right_index = current_index

        return left_index, right_index

    def _process_domain(self, result, domain):
        if domain and len(domain) == 3:
            field, operator, value = domain

            compute_operator = {
                'ilike': lambda field, value: str(value).lower() in str(field).lower(),
                'like': lambda field, value: str(value) in str(field),
                'not ilike': lambda field, value: str(value).lower() not in str(field).lower(),
                'not like': lambda field, value: str(value) not in str(field),
                '=': lambda field, value: value == field,
                '!=': lambda field, value: value != field,
                '>': lambda field, value: value < field,
                '<': lambda field, value: value > field,
                '>=': lambda field, value: value <= field,
                '<=': lambda field, value: value >= field,
            }

            operator = operator.lower()
            if field in result:
                if operator in compute_operator.iterkeys():
                    return compute_operator.get(operator)(result.get(field), value)

                raise osv.except_osv(u'错误', u'未添加的domain条件%s' % domain)

        raise osv.except_osv(u'错误', u'不可识别的domain条件，请检查domain"%s"是否正确' % domain)

    def _compute_domain_util(self, result, domains):
        index = 0
        while index < len(domains):
            domain = domains[index]
            index += 1
            if domain == '|':
                left_index, right_index = self.get_next_or_domain(domains, index)
                index = right_index

                if not self._compute_domain_util(result, domains[index:left_index]) and not self._compute_domain_util(result, domains[left_index:right_index]):
                    return False

            else:
                self.check_valid_domain(domain)
                if not self._process_domain(result, domain):
                    return False

        return True

    def _compute_domain(self, result, domain):
        return filter(lambda res: self._compute_domain_util(res, domain), result)

    def _compute_order(self, result, order):
        # TODO 暂时不支持多重排序
        if order:
            order = order.partition(',')[0].partition(' ')
            result.sort(key=lambda item: item.get(order[0]), reverse=order[2] == 'ASC')

        return result

    def _compute_limit_and_offset(self, result, limit, offset):
        return result[offset:limit + offset]

    def search_read(self, cr, uid, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        context = context or {}

        out_collection = self.collect_history_stock_by_sql(cr, sql_type='out', context=context)
        in_collection = self.collect_history_stock_by_sql(cr, sql_type='in', context=context)

        res = {}
        self.compute_history_stock_by_collect(res, in_collection, sql_type='in')
        self.compute_history_stock_by_collect(res, out_collection, sql_type='out')

        result = []
        for key, value in res.iteritems():
            value.update(self.unzip_record_key(key))
            result.append(value)

        result = self._compute_domain(result, domain)
        result = self._compute_order(result, order)
        result = self._compute_limit_and_offset(result, limit, offset)

        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
