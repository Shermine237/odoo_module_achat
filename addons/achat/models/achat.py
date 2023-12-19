# -*- coding: utf-8 -*-
from odoo import models, fields, api

class achat(models.Model):

    _inherit= 'purchase.order'

    type_commande= fields.Selection([
        ('antituberculeux', 'ANTITUBERCULEUX'),
        ('antirétroviraux et mio', 'ANTIRETROVIRAUX ET MIO'),
         ('antipaludéen', 'ANTIPALUDEEN'),
    ], string='Type de commande')
    partner_id=fields.Many2one(string='CENAME')
    product_id=fields.Many2one(string='Nom du DCI')
    partner_ref=fields.Char(string='Réference du CENAME')
    #aire_sante = fields.Char(string='Aire de santé')
    #region = fields.Char(string='Région')
    #district_sante = fields.Char(string='District de santé')
    #num_bc = fields.Char(string='N°BC')
    #periode_du=fields.Date(string='Période de couverture du')
    #periode_au=fields.Date(string='au')
    #nbre_patient=fields.Float(string='Nombre de patient')
    #consommation= fields.Float(string='Consommation')
    #cmm = fields.Float(string='CMM')
    #sdu_fin_3_mois = fields.Float(string='SDU fin du 3ème mois')
    #en_cours = fields.Float(string='En Cours')

def _afficher(self):
        for rec in self:
            if rec.type_commande == 'antituberculeux' or rec.type_commande == 'ANTITUBERCULEUX':
              self.name = ''
              self.aire_sante=''
            elif rec.type_commande == 'antirétroviraux et mio' or rec.type_commande == 'ANTIRETROVIRAUX ET MIO':
              self.name = ''
              self.aire_sante=''
            elif rec.type_commande == 'antipaludéen' or rec.type_commande == 'ANTIPALUDEEN':
              self.name = ''
              self.aire_sante=''
            else:
              self.name = ''
              self.aire_sante=''

    #order_lines = fields.One2many('achat.achatline','achat_id',string='Lignes de commande')


    #achat_id = fields.Many2one('achat.achat', string='Bon de commande')
    

    # order_lines = fields.One2many('achat.bon_commande.line', 'bon_commande_id', string='Lignes de commande')
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
