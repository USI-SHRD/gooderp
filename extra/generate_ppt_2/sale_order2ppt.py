# -*- coding: utf-8 -*-
from openerp.osv import fields
from openerp.osv import osv
from openerp import models, SUPERUSER_ID
from openerp.tools.translate import _
import os
import analyze_ppt
import urllib

class sale_order2ppt(models.TransientModel):
    _name = 'sale.order.ppt'
    _description = u'销售订单导出ppt方案'
    _columns = {
        'sale_order_ppt_char': fields.text(u'需要创建ppt方案的销售订单'),
    }
    _defaults = {
        'sale_order_ppt_char': lambda self, cr, uid, context={}: '丶'.join([sale_order.name for sale_order in self.pool.get('sale.order').browse(cr, uid, context.get('active_ids'), context=context)]),
    }


    def confirm_create_sale_order_ppt(self, cr, uid, ids, context=None):
        # 遍历当前激活或选中的订单
        for sale_order_obj in self.pool.get("sale.order").browse(
                cr, uid, context.get('active_ids'), context=context):
            # 当前文件所在目录
            curdirpath = os.path.dirname(__file__)
            template_file_path = os.path.join(curdirpath, 'static/files/dftg_template1.pptx')
            output_file_path = os.path.join(curdirpath, 'static/output/' + str(uid) + '_' + sale_order_obj.name + '.pptx')
            product_dicts = {}
            # 遍历找出所有订单行的产品信息
            for order_line_obj in sale_order_obj.order_line:
                product_dicts.setdefault(order_line_obj.product_id.id,order_line_obj.product_id)
            analyze_ppt.analyze_ppt(template_file_path, output_file_path, product_dicts)

            print "Begin download file============"
            ppt_url = "/PPT/get_ppt/"+str(uid) + '_' + sale_order_obj.name

            return {
                'type': 'ir.actions.act_url',
                'url': 'https://www.baidu.com',
                'target': 'self',
                'name': '123',
            }



class sale_order(osv.osv):
    _inherit = 'sale.order'
    def get_ppt_file(self, cr, uid, ids, context):
        sale_order2ppt = self.pool.get("sale.order.ppt")
        # 传入当前的订单ids
        context.update({"active_ids": ids})
        return sale_order2ppt.confirm_create_sale_order_ppt(cr, uid, ids, context)
