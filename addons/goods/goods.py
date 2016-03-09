# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class goods(osv.osv):
    _inherit = 'goods'

    _columns = {
        'using_batch': fields.boolean(u'批次管理'),
        'force_batch_one': fields.boolean(u'每批次数量为1'),
    }
