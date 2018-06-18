# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AssetTransferLine(models.Model):
    _name = 'asset.transfer.line'
    _description = 'Asset Transfer Line'
    _rec_name = 'asset_id'
    
    transfer_id = fields.Many2one('asset.transfer', string="Asset Transfer")
    distribution_id = fields.Many2one('asset.distribution', string="Request")
    name = fields.Char(string="Asset Transfer", related='transfer_id.name', readonly=True)
    asset_code = fields.Many2one('product.template', required=True, string="Asset Code", store=True)
    asset_id = fields.Many2one('product.product', string="Asset", compute='_compute_asset_id', store=True)    
    product_tmpl_id = fields.Many2one('product.template', string="Product Template", related='asset_id.product_tmpl_id',store=True)
    child_id = fields.Many2many('product.template', string="Child Assets")
    description = fields.Text('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
        ('collect', 'Collected'),
    ], index=True, readonly=True, copy=False, default='draft', required=True)
    date = fields.Date(string="Transfer Date", related='transfer_id.date', store=True)
    collected_date = fields.Date(string="Collected Date", related='transfer_id.collected_date', store=True)
    type = fields.Selection([
        ('new', 'Allocate New'),
        ('borrow', 'Allocation Borrowing'),
        ('collect_new', 'Allocation Collection'),
        ('collect_borrow', 'Borrowing Collection'),    
    ], string="Transfer Type", related='transfer_id.type', store=True)
    collected = fields.Boolean(string="Collected", related='transfer_id.collected')
    collected_count = fields.Integer(string="# of Collecting", compute='_count_collected', store=True)
    own_by = fields.Selection([
        ('employee', 'Employee'),
        ('project', 'Project'),
        ('department', 'Department'),
        ('customer', 'Customer'),
    ], string="Used By", related='transfer_id.own_by', store=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", related='transfer_id.employee_id', readonly=True, store=True)
    project_id = fields.Many2one('project.project', string="Project", related='transfer_id.project_id', readonly=True, store=True)
    department_id = fields.Many2one('hr.department', string="Department", related='transfer_id.department_id', readonly=True, store=True)
    partner_id = fields.Many2one('res.partner', string="Customer", related='transfer_id.partner_id', readonly=True, store=True)
    
    
    @api.depends('transfer_id.child_ids')
    def _count_collected(self):
        for r in self:
            r.collected_count = r.transfer_id.collected_count

    @api.onchange('asset_code')
    def onchange_asset_code(self):
        if self.asset_code:
            asset_id = self.env['product.product'].search([('product_tmpl_id', '=', self.asset_code.id)], limit=1)
            self.asset_id = asset_id.id

    @api.one
    @api.constrains('asset_code')
    def _compute_asset_id(self):
        if self.asset_code:
            asset_id = self.env['product.product'].search([('product_tmpl_id', '=', self.asset_code.id)], limit=1)
            self.asset_id = asset_id.id

    @api.onchange('asset_id')
    def onchange_asset_id(self):
        if self.asset_id:
            self.description = self.asset_id.description
            self.child_id = [(6, 0, [x.id for x in self.asset_id.child_id])]
        
    @api.multi
    def reject(self):
        for record in self:
            record.asset_id.write({
                'state': 'fail',
            })
            record.child_id.write({'state': 'fail'})
    
    @api.multi
    def done(self):
        asset_ids = []
        transfer_by = False
        history_obj = self.env['asset.history']        
        for record in self:
            history_type = ''
            if record.transfer_id.type == 'new':
                history_type = 'allocate'
            elif record.transfer_id.type == 'borrow':
                history_type = 'borrow'
            else:
                history_type = 'collect'
            asset_ids.append(record.asset_id.id)
            transfer_by = record.transfer_id.transfer_by
            retrieve_by = record.transfer_id.retrieve_by
            history_obj.create({
                'asset_id': record.asset_id.product_tmpl_id.id,
                'transfer_date': record.transfer_id.date,
                'retrieve_by': record.transfer_id.retrieve_by.id,
                'transfer_id': record.transfer_id.id,
                'type': history_type,
            })
         
        if not transfer_by.user_id:
            raise UserError(_("Please set Related User for Transfer By '%s'.") % transfer_by.name)
        if not retrieve_by.user_id:
            raise UserError(_("Please set Related User for Retrieve By '%s'.") % retrieve_by.name)
        child_state = False
           
        if self._context.get('collect')==True:
            self.env['product.product'].sudo().write({
                'state': 'available',})
            child_state = 'available'                                                                    
        else:
            self.env['product.product'].write({
                'own_by': record.transfer_id.own_by,
                'employee_id': record.transfer_id.employee_id.id or False,
                'project_id': record.transfer_id.project_id.id or False,
                'department_id': record.transfer_id.department_id.id or False,
                'partner_id': record.transfer_id.partner_id.id or False,
                'state': 'use', })
            
            child_state = 'use'
        if child_state:
            for r in self:
#                 change status of asset to available or use
                r.asset_id.write({'state': child_state})
                r.child_id.write({'state': child_state})
                if r.asset_id.parent_id:
                    r.asset_id.parent_id = False
        
        self.write({'state': 'done'})            
        return True
    
    @api.multi
    def cancel(self):
        history_obj = self.env['asset.history']
        for record in self:
            if record.transfer_id.type in ['new','borrow']:
                if record.transfer_id.distribution_id:
                    record.asset_id.write({
                        'state': 'book',
                    })
                    record.child_id.write({'state': 'book'})
                else:
                    record.asset_id.write({
                        'state': 'available',
                    })
                    record.child_id.write({'state': 'available'})
            if record.transfer_id.type in ['collect_new','collect_new']:
                record.asset_id.write({
                    'state': 'use',
                })
                record.child_id.write({'state': 'use'})
            
            #remove history
            history = history_obj.search([('transfer_id','=',record.transfer_id.id)])
            history.unlink()
            
        self.write({'state': 'cancel'})
        return True
    
    @api.multi
    def draft(self):
        self.write({'state': 'draft'})
        return True
    
    @api.multi
    def collect(self):
        self.write({'state': 'collect'})
        return True

    # @api.model
    # def create(self, vals):
    #     if 'asset_id' not in vals:
    #         vals['asset_id'] = self.asset_id.child_id
    #     return super(AssetTransferLine, self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     if 'asset_id' in vals:
    #         pass
    #     return super(AssetTransferLine, self).write(vals)