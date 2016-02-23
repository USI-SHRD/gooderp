# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class warehouse_picking(osv.osv):
    _name = 'warehouse.picking'

    _columns = {
        'name': fields.char(u'单据编号'),
        'partner_id': fields.many2one('partner', u'业务伙伴'),
        'date': fields.date(u'单据日期'),
        'create_uid': fields.many2one('res.users', u'制单人'),
        'create_date': fields.datetime(u'录单时间'),
        'write_uid': fields.many2one('res.users', u'最后修改人'),
        'write_date': fields.datetime(u'最后修改日期'),
        'approve_uid': fields.many2one('res.usres', u'审核人'),
        'move_out_ids': fields.one2many('warehouse.move', 'picking_out_id', u'明细'),
        'move_in_ids': fields.one2many('warehouse.move', 'picking_in_id', u'明细'),
        'note': fields.text(u'备注'),
    }
