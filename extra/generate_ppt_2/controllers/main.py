# -*- coding: utf-8 -*-

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp import SUPERUSER_ID
import simplejson
import random
import time
import datetime
import os
import sys

class PPTControllers(http.Controller):
    '''
        下载指定的ppt文件
    '''
    @http.route('/PPT/get_ppt/<ppt_id>', type='http', auth="user", methods=['GET'], website=True)
    def get_ppt(self, ppt_id, **kw):
        output_file_path = os.path.join(os.getcwd(),'odoo_addons/common_addons/generate_ppt/static/output/',ppt_id+'.pptx')
        print 'download file====2'
        file = open(output_file_path, 'r')
        return request.make_response(file,[('Content-Type', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')])
