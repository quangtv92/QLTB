# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AssetTransferReject(models.TransientModel):
    _name = 'asset.transfer.reject.wizard'
    
    reason = fields.Text(tring="Reason", required=True)
    
    @api.multi
    def reject_transfer(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []          
        for record in self.env['asset.transfer'].browse(active_ids):            
            record.reject(self.reason)
        return {'type': 'ir.actions.act_window_close'}