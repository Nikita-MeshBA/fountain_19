# -*- coding: utf-8 -*-
# from odoo import http


# class XeInternalProductRequest(http.Controller):
#     @http.route('/xe_internal_product_request/xe_internal_product_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/xe_internal_product_request/xe_internal_product_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('xe_internal_product_request.listing', {
#             'root': '/xe_internal_product_request/xe_internal_product_request',
#             'objects': http.request.env['xe_internal_product_request.xe_internal_product_request'].search([]),
#         })

#     @http.route('/xe_internal_product_request/xe_internal_product_request/objects/<model("xe_internal_product_request.xe_internal_product_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('xe_internal_product_request.object', {
#             'object': obj
#         })
