# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class warehouse_order(osv.osv):
    _name = 'warehouse.order'

    _inherits = {
        'warehouse.picking': 'picking_id',
    }

    OUTGOING_TYPE_SELECTION = [
        ('losses', u'盘亏'),
        ('others', u'其他出库'),
    ]

    INCOMING_TYPE_SELECTION = [
        ('overage', u'盘盈'),
        ('others', u'其他入库'),
    ]

    ORDER_TYPE = [
        ('outgoing', u'出库单'),
        ('incoming', u'入库单'),
        ('internal', u'内部调拨'),
    ]

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            move_ids = order.type == 'incoming' and order.move_in_ids or order.move_out_ids
            res.update({
                order.id: sum(move.price_subtotal for move in move_ids),
            })

        return res

    _columns = {
        'picking_id': fields.many2one('warehouse.picking', u'移库单', required=True, index=True, ondelete='cascade'),
        'outgoing_type': fields.selection(OUTGOING_TYPE_SELECTION, u'业务类别'),
        'incoming_type': fields.selection(INCOMING_TYPE_SELECTION, u'业务类别'),
        'type': fields.selection(ORDER_TYPE, u'单据类型'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
    }

    _defaults = {
        'type': 'internal',
    }
