# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class warehouse_picking(osv.osv):
    _name = 'warehouse_picking'

    OUTGOING_TYPE_SELECTION = [
        ('losses', u'盘亏'),
        ('others', u'其他出库'),
    ]

    INCOMING_TYPE_SELECTION = [
        ('overage', u'盘盈'),
        ('others', u'其他入库'),
    ]

    def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
        pass

    _columns = {
        'name': fields.char(u'单据编号'),
        'partner_id': fields.many2one('partner', u'业务伙伴'),
        'date': fields.date(u'单据日期'),
        'outgoing_type': fields.selection(OUTGOING_TYPE_SELECTION, u'业务类别'),
        'incoming_type': fields.selection(INCOMING_TYPE_SELECTION, u'业务类别'),
        'amount_total': fields.function(_get_amount_total, type='float', string=u'合计金额', digits_compute=dp.get_precision('Accounting')),
        'create_uid': fields.many2one('res.users', u'制单人'),
        'create_date': fields.datetime(u'录单时间'),
        'write_uid': fields.many2one('res.users', u'最后修改人'),
        'write_date': fields.datetime(u'最后修改日期'),
        'note': fields.text(u'备注'),
        'move_ids': fields.one2many('warehouse.move', 'picking_id', u'明细'),
    }
