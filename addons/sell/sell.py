# -*- encoding: utf-8 -*-

from openerp.osv import fields, osv

class sell_order(osv.osv):
    _name = 'sell.order'
    _description = "Sell Order"
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    _columns = {
                'name': fields.char(u'单据编号',copy=False),
                'partner_id': fields.many2one('partner',u'客户'),
                'staff_id': fields.many2one('staff',u'销售员'),
                'date': fields.date(u'单据日期',copy=False),
                'delivery_date': fields.date(u'交货日期'),
                'note': fields.text(u'备注'),
                'line_ids': fields.one2many('sell.order.line', 'order_id',u'销售订单行'),
                'benefit_rate': fields.float(u'优惠率(%)'),
                'benefit_amount': fields.float(u'优惠额'),
                'amount_total': fields.float(u'优惠后金额'),
                'create_user': fields.many2one('res.users',u'制单人'),
                'type': fields.selection([('sell',u'销货'),('return',u'退货')],u'订单类型'),
                'state': fields.selection([
                                          ('draft', u'未审批'),
                                          ('approved', u'已审批'),
                                          ('done', u'发货完成'),
                                           ], u'状态', readonly=True, copy=False)
                }
    _defaults = {
                 'date': fields.datetime.now,
                 'state': 'draft',
                 'name': lambda obj, cr, uid, context: '/',
                 'type': 'sell',
                 }
    
    _sql_constraints = [
                        ('name_uniq','unique(name)','销售订单号必须唯一！'),
                        ]
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sell.order', context=context)or '/'
        context = dict(context or {}, mail_create_nolog=True)
        order =  super(sell_order, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [order], body=u'销售单已创建', context=context)
        return order
    
    def submit_button(self, cr, uid, ids, context=None):
        '''对销货订单的提交审核按钮，还需修改'''
        self.write(cr, uid, ids, {'state':'approved'}, context=context)
        return  
    
    def onchange_benefit_rate(self, cr, uid, ids, benefit_rate, context=None):
         '''当优惠率改变时，改变优惠金额和优惠后金额'''
         total = 0
         for line in self.browse(cr, uid, ids, context=context).line_ids:
             total += line.tax_amount_total
         benefit_amount = total * benefit_rate * 0.01
         return {'value':{
                          'benefit_amount': benefit_amount,
                          'amount_total': total - benefit_amount,
                          }
                 }  
    
        
class sell_order_line(osv.osv):
    _name = 'sell.order.line'
    _description = u'销货订单明细'
    _columns = {
                'order_id': fields.many2one('sell.order',u'销售订单'),
                'goods_id': fields.many2one('goods',u'商品'),
                'spec': fields.char(u'属性'),#产品的属性，选择产品时自动从产品管理表获取
                'uom_id': fields.many2one('uom',u'单位'),
                'warehouse_id': fields.many2one(u'warehouse',u'仓库'),
                'quantity': fields.float(u'数量'),
                'price': fields.float(u'销售单价'),
                'discount_rate': fields.float(u'折扣率(%)'),
                'discount_amount': fields.float(u'折扣额'),
                'amount': fields.float(u'金额'),
                'tax_rate': fields.float(u'税率(%)'),
                'tax_amount': fields.float(u'税额'),
                'tax_amount_total': fields.float(u'价税合计'),                
                }
    
    def onchange_price(self, cr, uid, ids, price, quantity, discount_rate, tax_rate, context=None):
        '''当销货单价，数量，折扣率，税率改变时，改变折扣额，金额，税额，价税合计'''
        amt = price * quantity
        discount_amt = amt * discount_rate * 0.01
        amount = amt - discount_amt
        tax_amt = amount * tax_rate * 0.01
        return {'value':{
                         'discount_amount': discount_amt,
                         'amount': amount,
                         'tax_amount': tax_amt,
                         'tax_amount_total': amount + tax_amt,
                         }
                }
