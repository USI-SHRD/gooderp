# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class wh_move(osv.osv):
    _name = 'wh.move'

    def approve_order(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            order.line_out_ids.action_done()
            order.line_in_ids.action_done()

        return self.write(cr, uid, ids, {
                'approve_uid': uid,
                'approve_date': fields.datetime.now(cr, uid),
                'state': 'done',
            })

    def cancel_approved_order(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            order.line_out_ids.action_cancel()
            order.line_in_ids.action_cancel()

        return self.write(cr, uid, ids, {
                'approve_uid': False,
                'approve_date': False,
                'state': 'draft',
            })

    MOVE_STATE = [
        ('draft', u'草稿'),
        ('done', u'已审核'),
    ]

    _columns = {
        'name': fields.char(u'单据编号', copy=False),
        'state': fields.selection(MOVE_STATE, u'状态', copy=False),
        'partner_id': fields.many2one('partner', u'业务伙伴'),
        'date': fields.date(u'单据日期', copy=False),
        'approve_uid': fields.many2one('res.users', u'审核人', copy=False),
        'approve_date': fields.datetime(u'审核日期', copy=False),
        'line_out_ids': fields.one2many('wh.move.line', 'move_id', u'明细', domain=[('type', '=', 'out')], context={'type': 'out'}),
        'line_in_ids': fields.one2many('wh.move.line', 'move_id', u'明细', domain=[('type', '=', 'in')], context={'type': 'in'}),
        'note': fields.text(u'备注'),
    }

    _defaults = {
        'name': '/',
        'date': fields.date.context_today,
        'state': 'draft',
    }
