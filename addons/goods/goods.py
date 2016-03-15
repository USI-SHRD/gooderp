# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields


class goods(osv.osv):
    _inherit = 'goods'

    _columns = {
        'using_batch': fields.boolean(u'批次管理'),
        'force_batch_one': fields.boolean(u'每批次数量为1'),
        'attribute_ids':fields.one2many('attribute','goods_id',string=u'属性'),
    }

class attribute(osv.osv):
    _name = 'attribute'
    _columns = {
        'name':fields.char('名称'),
        'goods_id':fields.many2one('goods',u'商品'),
        'value_ids':fields.one2many('attribute.value','attribute_id',string=u'属性'),
    }
class attribute_value(osv.osv):
    _name = 'attribute.value'
    _rec_name = 'value_id'
    _columns = {
        'attribute_id':fields.many2one('attribute',u'属性'),
        'category_id': fields.many2one('core.category',u'属性',
                                       domain=[('type','=','attribute')],context={'type':'attribute'}
                                       ,required='1'),
        'value_id': fields.many2one('core.value',u'值',
                                       domain=[('type','=','attribute')],context={'type':'attribute'}
                                       ,required='1'),
    }