# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
from utils import inherits, inherits_after
import openerp.addons.decimal_precision as dp


class wh_out(osv.osv):
    _name = 'wh.out'

    _inherits = {
        'wh.move': 'move_id',
    }

    TYPE_SELECTION = [
        ('losses', u'盘亏'),
        ('others', u'其他出库'),
    ]

    @inherits()
    def approve_order(self, cr, uid, ids, context=None):
        return True

    @inherits()
    def cancel_approved_order(self, cr, uid, ids, context=None):
        return True

    @inherits_after()
    def unlink(self, cr, uid, ids, context=None):
        return super(wh_out, self).unlink(cr, uid, ids, context=context)

    def get_line(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            yield order, order.line_out_ids

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order, lines in self.get_line(cr, uid, ids, context=context):
            res.update({
                order.id: sum(line.subtotal for line in lines),
            })

        return res

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'type': fields.selection(TYPE_SELECTION, u'业务类别'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
    }

    _defaults = {
        'type': 'others',
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals.update({'name': self.pool.get('ir.sequence').get(cr, uid, self._name, context=context) or '/'})

        return super(wh_out, self).create(cr, uid, vals, context=context)


class wh_in(osv.osv):
    _name = 'wh.in'

    _inherits = {
        'wh.move': 'move_id',
    }

    TYPE_SELECTION = [
        ('overage', u'盘盈'),
        ('others', u'其他入库'),
    ]

    @inherits()
    def approve_order(self, cr, uid, ids, context=None):
        return True

    @inherits()
    def cancel_approved_order(self, cr, uid, ids, context=None):
        return True

    @inherits_after()
    def unlink(self, cr, uid, ids, context=None):
        return super(wh_in, self).unlink(cr, uid, ids, context=context)

    def get_line(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            yield order, order.line_in_ids

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order, lines in self.get_line(cr, uid, ids, context=context):
            res.update({
                order.id: sum(line.subtotal for line in lines),
            })

        return res

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'type': fields.selection(TYPE_SELECTION, u'业务类别'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
    }

    _defaults = {
       'type': 'others',
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals.update({'name': self.pool.get('ir.sequence').get(cr, uid, self._name, context=context) or '/'})

        return super(wh_in, self).create(cr, uid, vals, context=context)


class wh_internal(osv.osv):
    _name = 'wh.internal'

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
        return super(wh_internal, self).unlink(cr, uid, ids, context=context)

    def get_line(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            yield order, order.line_out_ids

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order, lines in self.get_line(cr, uid, ids, context=context):
            res.update({
                order.id: sum(line.subtotal for line in lines),
            })

        return res

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals.update({'name': self.pool.get('ir.sequence').get(cr, uid, self._name, context=context) or '/'})

        return super(wh_internal, self).create(cr, uid, vals, context=context)
