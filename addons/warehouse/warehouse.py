# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class warehouse(osv.osv):
    _inherit = 'warehouse'

    _columns = {
        'name': fields.char(u'仓库名称'),
        'code': fields.char(u'仓库编号'),
        'active': fields.boolean(u'有效'),
    }

    _defaults = {
        'active': True,
    }
