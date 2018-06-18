# -*- coding: utf-8 -*-

from odoo import fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class AssetHistory(models.Model):
    _name = 'asset.history'
    _description = 'asset.history'
    _order = 'date desc'
    
    asset_id = fields.Many2one('product.template', string="Asset")
    name = fields.Char(string="Name", related='asset_id.name', readonly=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now())
    transfer_date = fields.Date(string="Transfer Date")
    retrieve_by = fields.Many2one('hr.employee', string="Retrieve By")
    transfer_id = fields.Many2one('asset.transfer', string="Transfer Reference")
    type = fields.Selection([
        ('allocate','Allocation'),
        ('borrow','Borrowing'),
        ('collect','Collected'),
    ], string="Type")