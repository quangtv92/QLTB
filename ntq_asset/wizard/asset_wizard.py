# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class asset_wizard(models.TransientModel):
    _name = 'asset.wizard'
    _description = 'Asset Wizard'
    
    type = fields.Selection([
        ('new', 'New Asset'),
        ('use', 'Use Asset'),
        ('repair', 'Repair Asset'),
        ('lost', 'Lost'),
        ('liquidated', 'Liquidated'),
        ('disposed', 'Disposed'),
    ], string="Wizard Type", required=True)
    origin = fields.Selection([
        ('buy', 'Buy'),
        ('gift', 'Gift'),
        ('rent', 'Rent'),
        ('borrow', 'Borrow'),
    ], sring="Origin", required=True, default='buy')
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order", domain=[('state','in',['purchase','done'])])
    purchase_date = fields.Date(string="Purchase Date")
    request_by = fields.Many2one('hr.employee', string="Request By")
    request_date = fields.Date(string="Request Date")
    approve_request_by = fields.Many2one('hr.employee', string="Approve By")
    origin_partner_id = fields.Many2one('res.partner', string="Partner")
    origin_date = fields.Date(string="Date")
    available_date = fields.Date(string="Available Date")
    own_by = fields.Selection([
        ('employee', 'Employee'),
        ('project', 'Project'),
        ('department', 'Department'),
        ('company', 'Company'),
        ('customer', 'Customer'),
    ], string="Own By", required=True, default='employee')
    employee_id = fields.Many2one('hr.employee', string="Employee")
    project_id = fields.Many2one('project.project', string="Project")
    department_id = fields.Many2one('hr.department', string="Department")
    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer','=',True)])
    lost_date = fields.Date(string="Lost Date", default=fields.Date.today)
    liquidated_date = fields.Date(string="Liquidated Date", default=fields.Date.today)
    disposed_date = fields.Date(string="Disposed Date", default=fields.Date.today)
    reason = fields.Text(string="Reason")
    responsible = fields.Many2one('hr.employee', string="Responsible")
    standard_price = fields
    
    @api.onchange('purchase_order_id')
    def onchange_purchase_order(self):
        self.purchase_date = self.purchase_order_id.date_order
    
    @api.model
    def prepare_new_asset(self):
        res = {
            'origin': self.origin,
            'purchase_order_id': self.purchase_order_id.id,
            'purchase_date': self.purchase_date,
            'request_by': self.request_by.id,
            'request_date': self.request_date,
            'approve_request_by': self.approve_request_by.id,
            'origin_partner_id': self.origin_partner_id.id,
            'origin_date': self.origin_date,
            'available_date': self.available_date,
        }
        return res
        
    @api.model
    def prepare_use_asset(self):
        res = {
            'own_by': self.own_by,
            'employee_id': self.employee_id.id,
            'project_id': self.project_id.id,
            'department_id': self.department_id.id,
            'partner_id': self.partner_id.id,
            'available_date': self.available_date,
        }
        return res
    
    @api.model
    def prepare_repair_asset(self):
        res = {'available_date': self.available_date}
        return res
    
    @api.one
    def apply_asset_wizard(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', []) or []
        asset = self.env['product.template'].browse(active_id)
        if self.type == 'new':
            vals = self.prepare_new_asset()
            asset.write(vals)
            asset.new_asset()
        elif self.type == 'use':
            vals = self.prepare_use_asset()
            asset.write(vals)
            asset.use_asset()
        elif self.type == 'repair':
            vals = self.prepare_repair_asset()
            asset.write(vals)
            asset.repair_asset()
        elif self.type == 'lost':
            asset.lost_asset(self.reason, self.lost_date, self.responsible)
        elif self.type == 'liquidated':
            asset.liquidate_asset(self.reason, self.liquidated_date, self.responsible)
        elif self.type == 'disposed':
            asset.dispose_asset(self.reason, self.disposed_date)
        