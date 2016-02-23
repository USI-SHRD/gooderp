# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

CORE_CATEGORY_TYPE = [('customer',u'客户'),
                      ('supplier',u'供应商'),
                      ('goods',u'商品'),
                      ('payment',u'支出'),
                      ('receipt',u'收入'),]
CORE_COST_METHOD = [('average',u'移动平均法'),
                    ('fifo',u'先进先出法'),
                    ]
class core_value(osv.osv):
    _name = 'core.value'
    _columns = {
        'name': fields.char(u'名称'),
        'type': fields.char(u'类型'),
               }
    _defaults = {
        'type':lambda self, cr, uid, ctx:ctx.get('type'),
    }
class core_category(osv.osv):
    _name = 'core.category'
    _columns = {
        'name': fields.char(u'名称'),
        'type': fields.selection(CORE_CATEGORY_TYPE,u'类型'),
               }
    _defaults = {
        'type':lambda self, cr, uid, ctx:ctx.get('type'),
    }
class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'start_date':fields.date(u'启用日期'),
        'quantity_digits':fields.integer(u'数量小数位'),
        'amount_digits':fields.integer(u'单价小数位'),
        'cost_method':fields.selection(CORE_COST_METHOD,u'存货计价方法'),
        'negtive_quantity':fields.boolean(u'是否检查负库存'),
        }
class uom(osv.osv):
    _name = 'uom'
    _columns = {
        'name':fields.char(u'名称'),
                }
class settle_mode(osv.osv):
    name = 'settle.mode'
    _columns = {
        'name':fields.char(u'名称'),
                }
class partner(osv.osv):
    _name = 'partner'
    _columns = {
        'name': fields.char(u'名称'),
        'c_category_id': fields.many2one('core.category',u'客户类别',
                                       domain=[('type','=','customer')],context={'type':'customer'}),
        's_category_id': fields.many2one('core.category',u'供应商类别',
                                       domain=[('type','=','supplier')],context={'type':'supplier'}),
               }
class goods(osv.osv):
    _name = 'goods'
    _columns = {
        'name':fields.char(u'名称'),
        'uom_id':fields.many2one('uom',u'计量单位'),
                }
class warehouse(osv.osv):
    _name = 'warehouse'
    _columns = {
        'name':fields.char(u'名称'),
                }
class staff(osv.osv):
    _name = 'staff'
    _columns = {
        'name': fields.char(u'名称'),
                }    
class bank_account(osv.osv):
    _name = 'bank.account'
    _columns = {
        'name':fields.char(u'名称'),
                }