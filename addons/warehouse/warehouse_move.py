# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class wh_move(osv.osv):
    _name = 'wh.move'

    def get_line(self, cr, uid, ids, context=None):
        raise NotImplementedError()

    def approve_order(self, cr, ids, context=None):
        raise NotImplementedError()

    _columns = {
        'name': fields.char(u'单据编号'),
        'partner_id': fields.many2one('partner', u'业务伙伴'),
        'date': fields.date(u'单据日期'),
        'approve_uid': fields.many2one('res.usres', u'审核人'),
        'approve_date': fields.datetime(u'审核日期'),
        'line_out_ids': fields.one2many('wh.move.line', 'move_id', u'明细', domain=[('type', '=', 'out')], context={'type': 'out'}),
        'line_in_ids': fields.one2many('wh.move.line', 'move_id', u'明细', domain=[('type', '=', 'in')], context={'type': 'in'}),
        'note': fields.text(u'备注'),
    }

    _defaults = {
        'name': '/',
        'date': fields.date.context_today,
    }
