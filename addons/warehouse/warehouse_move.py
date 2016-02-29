# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class wh_move(osv.osv):
    _name = 'wh.move'

    def unlink(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            if move.state == 'done':
                raise osv.except_osv(u'错误', u'不可以删除已经完成的单据')

        return super(wh_move, self).unlink(cr, uid, ids, context=context)

    def prev_approve_order(self, cr, uid, ids, context=None):
        pass

    def approve_order(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            order.prev_approve_order()
            order.line_out_ids.action_done()
            order.line_in_ids.action_done()

        return self.write(cr, uid, ids, {
                'approve_uid': uid,
                'approve_date': fields.datetime.now(cr, uid),
                'state': 'done',
            })

    def prev_cancel_approved_order(self, cr, uid, ids, context=None):
        pass

    def cancel_approved_order(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            order.prev_cancel_approved_order()
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
        'line_out_ids': fields.one2many('wh.move.line', 'move_id', u'明细', domain=[('type', '=', 'out')], context={'type': 'out'}, copy=True),
        'line_in_ids': fields.one2many('wh.move.line', 'move_id', u'明细', domain=[('type', '=', 'in')], context={'type': 'in'}, copy=True),
        'note': fields.text(u'备注'),
    }

    _defaults = {
        'name': '/',
        'date': fields.date.context_today,
        'state': 'draft',
    }
