# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AssetGenerateEntry(models.TransientModel):
    _name = 'asset.generate.entry.wizard'
    _description = 'Asset Generate Gift Entry'
    
    journal_id = fields.Many2one('account.journal', domain=[('type','not in',['cash','bank'])], required=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    ref = fields.Char(string="Reference", required=True)
    value = fields.Float(string="Value", readonly=True, digits=(16,0))
    
    def _prepare_move_line(self, asset):
        '''
        This function prepares move line of account.move related to an gift asset
        '''
        partner_id = asset.origin_partner_id.id or False
        res = []
        
        # debit journal item
        res.append((0, 0, {
            'date_maturity': self.date,
            'partner_id': partner_id,
            'name': self.ref,
            'debit': self.value,
            'credit': 0,
            'account_id': asset.categ_id.property_stock_valuation_account_id.id,
            'ref': self.ref,
            'quantity': 1,
        }))
        
        # credit journal item
        res.append((0, 0, {
            'date_maturity': self.date,
            'partner_id': partner_id,
            'name': self.ref,
            'debit': 0,
            'credit': self.value,
            'account_id': self.journal_id.default_credit_account_id.id,
            'ref': self.ref,
            'quantity': 1,
        }))
        return res
    
    @api.model
    def _prepare_move(self, asset):
        res = {
            'journal_id': self.journal_id.id,
            'company_id': self.env.user.company_id.id,
            'date': self.date,
            'ref': self.ref,
            'line_ids': self._prepare_move_line(asset),
        }
        return res
    
    @api.one
    def generate_entry(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', []) or []
        asset = self.env['product.template'].browse(active_id)
        
        if not self.journal_id.default_credit_account_id:
            raise UserError(_("You must define default credit account for '%s'.") % self.journal_id.name)
        if not asset.categ_id.property_stock_valuation_account_id:
            raise UserError(_("You must define stock valuation account for category '%s'.") % asset.categ_id.name)
        
        vals = self._prepare_move(asset)
        move = self.env['account.move'].create(vals)
        move.post()
        asset.generate_entry(move)