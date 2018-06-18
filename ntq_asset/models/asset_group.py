# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AssetGroup(models.Model):
    _name = 'asset.group'
    _description = 'Asset Group'
    
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
    line_ids = fields.One2many('asset.group.line', 'group_id', string="Group Details")
    
class AssetGroupLine(models.Model):
    _name = 'asset.group.line'
    _description = 'Asset Group Details'
    
    group_id = fields.Many2one('asset.group', string="Group", index=True)
    asset_categ_id = fields.Many2one('product.category', string="Asset Category", required=True, domain=[('is_asset','=',True)])
    name = fields.Text(string="Description", required=True)
    
    @api.onchange('asset_id')
    def onchange_asset(self):
        self.name = self.asset_id.description