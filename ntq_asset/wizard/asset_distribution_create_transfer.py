# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AssetDistributionCreateTransfer(models.TransientModel):
    _name = 'asset.distribution.create.transfer'
    
    @api.model
    def _default_transfer_by(self):
        employee = self.env['hr.employee'].search([('user_id','=', self.env.user.id)], limit=1)
        return employee or False
    
    @api.model
    def _default_retrieve_by(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', []) or []
        distribution = self.env['asset.distribution'].browse(active_id)
        if distribution.distrubute_to == 'employee':
            return distribution.employee_id
        return False
    
    transfer_by = fields.Many2one('hr.employee', string="Transfer By", required=True, default=_default_transfer_by)
    retrieve_by = fields.Many2one('hr.employee', string="Retrieve By", required=True, default=_default_retrieve_by)
    collected_date = fields.Date(string="Collected Date")
    date = fields.Date(string="Transfer Date", required=True, default=fields.Date.today)
    own_by = fields.Selection([
        ('employee', 'Employee'),
        ('project', 'Project'),
        ('department', 'Department'),
        ('customer', 'Customer'),
    ], string="Own By", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    project_id = fields.Many2one('project.project', string="Project")
    department_id = fields.Many2one('hr.department', string="Department")
    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer','=',True)])
    reason = fields.Text(string="Reason")
    journal_id = fields.Many2one('account.journal', string="Transfer Journal", required=True)
    memo = fields.Char(string="Memo")
    it_check = fields.Boolean(string="Require IT Check", default=True)
    assign_to = fields.Many2one('hr.employee', string="Assign To")
    type = fields.Selection([
        ('new', 'New'),
        ('borrow', 'Borrow'),
        ('collect_new', 'Allocation Collection'),
        ('collect_borrow', 'Borrowing Collection'),
    ], string="Transfer Type", required=True)
    parent_id = fields.Many2one('asset.transfer', 'Agreement')    
    
    @api.onchange('it_check')
    def onchange_it_check(self):
        if self.it_check:
            model_data = self.env['ir.model.data']
            it_group_id = model_data.xmlid_to_res_id('base.group_asset_it', raise_if_not_found=True)
            it_group = self.env['res.groups'].browse(it_group_id)
            user_ids = [x.id for x in it_group.users]
            return {'domain': {'assign_to': [('user_id','in',user_ids)]}}
    
    @api.model
    def _prepare_transfer_line(self, distribution):
        res = []
        for line in distribution.line_ids:
            res.append((0, 0, {
                'asset_id': line.asset_id.id,
                'child_id': [(6, 0, [x.id for x in line.child_id])],
                'description': line.name,
            }))
        return res
    
    @api.model
    def _prepare_transfer(self, distribution=None):
        res = {
            'distribution_id': distribution and distribution.id or False,
            'transfer_by': self.transfer_by.id,
            'retrieve_by': self.retrieve_by.id,
            'own_by': self.own_by,
            'employee_id': self.employee_id.id,
            'project_id': self.project_id.id,
            'department_id': self.department_id.id,
            'partner_id': self.partner_id.id,
            'reason': self.reason,
            'journal_id': self.journal_id.id,
            'memo': self.memo,
            'date': self.date,
            'line_ids': distribution and self._prepare_transfer_line(distribution) or [],
            'it_check': self.it_check,
            'assign_to': self.assign_to.id,
            'type': self.type,
            'parent_id': self.parent_id.id,
            'collected_date': self.collected_date,
        }
        return res
    
    @api.multi
    def transfer(self):
        self.ensure_one()
        context = dict(self._context or {})
        if self.type in ['new', 'borrow']:
            active_id = context.get('active_id', []) or []
            distribution = self.env['asset.distribution'].browse(active_id)
            distribution.transfer()
            vals = self._prepare_transfer(distribution)
        if self.type in ['collect_new','collect_borrow']:
            vals = self._prepare_transfer()
        transfer = self.env['asset.transfer'].create(vals)
        if self.type in ['new', 'borrow']:
            transfer.transfer_confirm()        
        return {'type': 'ir.actions.act_window_close'}