# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AssetDistributionReject(models.TransientModel):
    _name = 'asset.distribution.reject.wizard'
    
    reason = fields.Text(tring="Reason", required=True)
    
    @api.multi
    def reject_distribution(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []          
        for record in self.env['asset.distribution'].browse(active_ids):
            if record.state not in ['waiting','approve']:
                raise UserError(_("You cannot reject a distribution which has not Waiting Approval or Approved."))
            record.reject(self.reason)
        return {'type': 'ir.actions.act_window_close'}