# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AssetCategory(models.Model):
    _inherit = 'product.category'
    
    @api.model
    def _default_code(self):
        model_data = self.env['ir.model.data']
        code_id = model_data.xmlid_to_object('ntq_asset.seq_asset_category', raise_if_not_found=False)
        return code_id
    
    is_asset = fields.Boolean(string="Is Asset Category?")
    code = fields.Many2one('ir.sequence', string='Code', required=True, default=_default_code)
    description = fields.Text(string="Ghi chú")
    
    _sql_constraints = [
        ('name_unique',
         'unique(name)',
         'The category has already'),
    ]