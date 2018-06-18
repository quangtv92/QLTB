# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AssetDistributionLine(models.Model):
    _name = 'asset.distribution.line'
    _description = 'Asset Distribution Line'
    _order = 'deadline, expired_date, distribution_id'
    
    distribution_id = fields.Many2one('asset.distribution', string="Distribution", index=True)
    asset_id = fields.Many2one('product.product', string="Asset")
    asset_code = fields.Char(string="Asset Code", related='asset_id.asset_code', store=True)
    product_tmpl_id = fields.Many2one('product.template', string="Product Template", related='asset_id.product_tmpl_id', store=True)
    child_id = fields.Many2many('product.template', string="Child Assets")
    distribute_date = fields.Date(string="Request Date", related='distribution_id.distribute_date', readonly=True, store=True)
    deadline = fields.Date(string="Deadline", related='distribution_id.deadline', readonly=True, store=True)
    expired_date = fields.Date(string="Collected Date")
    borrow_date = fields.Date(string="Borrow Date", related='distribution_id.borrow_date', readonly=True, store=True)
    name = fields.Text(string="Description")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled'),
        ('approve', 'Approved'),
        ('waiting_avai', 'Waiting Availability'),
        ('available', 'Available'),
        ('transfer', 'Transfered'),
        ('collect', 'Collected')
    ], string="Status", index=True, readonly=True, copy=False, default='draft', required=True)
    asset_state = fields.Selection([
        ('draft', 'Draft'),
        ('new', 'New'),
        ('available', 'Available'),
        ('use', 'In Use'),
        ('repair', 'Repair'),
        ('lost', 'Lost'),
        ('liquidated', 'Liquidated'),
        ('disposed', 'Disposed'),
        ('cancel', 'Canceled')
    ], string="Asset Status", related='asset_id.state', readonly=True)
    type = fields.Selection([
        ('new', 'New'),
        ('borrow', 'Borrow')
    ], string="Distribution Type", related='distribution_id.type', store=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Priority", related='distribution_id.priority', readonly=True, store=True)
    distrubute_to = fields.Selection([
        ('employee', 'Employee'),
        ('project', 'Project'),
        ('department', 'Department')
    ], string="Allocate To", related='distribution_id.distrubute_to', readonly=True, store=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", related='distribution_id.employee_id', readonly=True, store=True)
    project_id = fields.Many2one('project.project', string="Project", related='distribution_id.project_id', readonly=True, store=True)
    department_id = fields.Many2one('hr.department', string="Department", related='distribution_id.department_id', readonly=True, store=True)
    asset_group_id = fields.Many2one('asset.group', string="Asset Group", related='distribution_id.asset_group_id', readonly=True, store=True)
    
    _sql_constraints = [
        ('asset_unique',
         'unique(distribution_id,asset_id)',
         'The asset cannot duplicate'),
    ]
    
    @api.onchange('asset_id')
    def onchange_asset_id(self):
        if self.asset_id:
            self.name = self.asset_id.description
            self.child_id = [(6, 0, [x.id for x in self.asset_id.child_id])]
    
    @api.multi
    def set_to_book(self):
        for record in self:
            if record.asset_id and record.asset_id.state in ['available','new']:
                record.asset_id.product_tmpl_id.write({'state': 'book'})
                record.child_id.write({'state': 'book'})
                
    @api.multi
    def set_to_available(self):
        for record in self:
            if record.asset_id and record.asset_id.state == 'book':
                record.asset_id.write({'state': 'available'})
                record.child_id.write({'state': 'available'})
    
    @api.model
    def create(self, vals):
        if 'state' in vals:
            if vals['state'] is False:
                vals['state'] = 'draft'
        return super(AssetDistributionLine, self).create(vals)