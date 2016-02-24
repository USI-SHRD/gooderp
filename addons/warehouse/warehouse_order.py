# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class wh_order_out(osv.osv):
    _name = 'wh.order.out'

    _inherits = {
        'wh.move': 'move_id',
    }

    TYPE_SELECTION = [
        ('losses', u'盘亏'),
        ('others', u'其他出库'),
    ]

    def get_line(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            yield order, order.line_out_ids

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order, lines in self.get_line(cr, uid, ids, context=context):
            res.update({
                order.id: sum(line.price_subtotal for line in lines),
            })

        return res

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'type': fields.selection(TYPE_SELECTION, u'业务类别'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
    }


class wh_order_in(osv.osv):
    _name = 'wh.order.in'

    _inherits = {
        'wh.move': 'move_id',
    }

    TYPE_SELECTION = [
        ('overage', u'盘盈'),
        ('others', u'其他入库'),
    ]

    def get_line(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            yield order, order.line_in_ids

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order, lines in self.get_line(cr, uid, ids, context=context):
            res.update({
                order.id: sum(line.price_subtotal for line in lines),
            })

        return res

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'type': fields.selection(TYPE_SELECTION, u'业务类别'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
    }


class wh_order_internal(osv.osv):
    _name = 'wh.order.internal'

    _inherits = {
        'wh.move': 'move_id',
    }

    def get_line(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            yield order, order.line_out_ids

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order, lines in self.get_line(cr, uid, ids, context=context):
            res.update({
                order.id: sum(line.price_subtotal for line in lines),
            })

        return res

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
    }
