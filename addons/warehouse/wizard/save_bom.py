# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class save_bom_memory(osv.osv_memory):
    _name = 'save.bom.memory'

    def save_bom(self, cr, uid, ids, context=None):
        for bom in self.browse(cr, uid, ids, context=context):
            return self.pool.get(context.get('active_model')).save_bom(
                cr, uid, context.get('active_ids'), bom.name, context=context)

    _columns = {
        'name': fields.char(u'模板名称'),
    }
