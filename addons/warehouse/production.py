# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
from utils import inherits, inherits_after
import openerp.addons.decimal_precision as dp


class wh_assembly(osv.osv):
    _name = 'wh.assembly'

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
        return super(wh_assembly, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'fee': fields.float(u'组装费用', digits_compute=dp.get_precision('Accounting')),
    }


class wh_disassembly(osv.osv):
    _name = 'wh.disassembly'

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
        return super(wh_disassembly, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'move_id': fields.many2one('wh.move', u'移库单', required=True, index=True, ondelete='cascade'),
        'fee': fields.float(u'拆卸费用', digits_compute=dp.get_precision('Accounting')),
    }
