# -*- coding: utf-8 -*-
# from odoo import http


# class Achat(http.Controller):
#     @http.route('/achat/achat', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/achat/achat/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('achat.listing', {
#             'root': '/achat/achat',
#             'objects': http.request.env['achat.achat'].search([]),
#         })

#     @http.route('/achat/achat/objects/<model("achat.achat"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('achat.object', {
#             'object': obj
#         })
