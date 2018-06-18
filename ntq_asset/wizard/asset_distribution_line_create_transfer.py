# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AssetDistributionLineCreateTransfer(models.TransientModel):
    _name = 'asset.distribution.line.create.transfer'
    
    @api.model
    def _default_transfer_by(self):
        context = dict(self._context or {})
        default_type = context.get('default_type', False)
        if not default_type:            
            employee = self.env['hr.employee'].search([('user_id','=', self.env.user.id)], limit=1)
            return employee or False
        elif default_type == 'collect_borrow':
            active_ids = context.get('active_ids', []) or []
            lines = self.env['asset.transfer.line'].browse(active_ids)
            if lines:
                return lines[0].transfer_id.retrieve_by
            
        return False
    
    @api.model
    def _default_retrieve_by(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if not default_type:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            if lines:
                if lines[0].distribution_id.distrubute_to == 'employee':
                    return lines[0].distribution_id.employee_id
        elif default_type == 'collect_borrow':
            lines = self.env['asset.transfer.line'].browse(active_ids)
            if lines:
                return lines[0].transfer_id.transfer_by
        return False
    
    @api.model
    def _default_collected_date(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if not default_type:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            if lines:
                return lines[0].distribution_id.expired_date
        return False    
    
    @api.model
    def _default_type(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if not default_type:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            if lines:
                return lines[0].distribution_id.type
        elif default_type == 'collect_borrow':
            return type
        return False
    
    @api.model
    def _default_own_by(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if not default_type:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            if lines:
                return lines[0].distribution_id.distrubute_to
        elif default_type == 'collect_borrow':
            lines = self.env['asset.transfer.line'].browse(active_ids)
            if lines:
                return lines[0].transfer_id.own_by
            
    @api.model
    def _default_employee_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if not default_type:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            if lines:
                return lines[0].distribution_id.employee_id
        elif default_type == 'collect_borrow':
            lines = self.env['asset.transfer.line'].browse(active_ids)
            if lines:
                return lines[0].transfer_id.employee_id
            
    @api.model
    def _default_project_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if not default_type:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            if lines:
                return lines[0].distribution_id.project_id
        elif default_type == 'collect_borrow':
            lines = self.env['asset.transfer.line'].browse(active_ids)
            if lines:
                return lines[0].transfer_id.project_id
            
    @api.model
    def _default_department_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if not default_type:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            if lines:
                return lines[0].distribution_id.department_id
        elif default_type == 'collect_borrow':
            lines = self.env['asset.transfer.line'].browse(active_ids)
            if lines:
                return lines[0].transfer_id.department_id
            
    @api.model
    def _default_partner_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        default_type = context.get('default_type', False)
        if default_type == 'collect_borrow':
            lines = self.env['asset.transfer.line'].browse(active_ids)
            if lines:
                return lines[0].transfer_id.partner_id
    
    transfer_by = fields.Many2one('hr.employee', string="Transfer By", required=True, default=_default_transfer_by)
    retrieve_by = fields.Many2one('hr.employee', string="Retrieve By", required=True, default=_default_retrieve_by)
    date = fields.Date(string="Transfer Date", required=True, default=fields.Date.today)
    own_by = fields.Selection([
        ('employee', 'Employee'),
        ('project', 'Project'),
        ('department', 'Department'),
        ('customer', 'Customer'),
    ], string="Own By", required=True, default=_default_own_by)
    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee_id)
    project_id = fields.Many2one('project.project', string="Project", default=_default_project_id)
    department_id = fields.Many2one('hr.department', string="Department", default=_default_department_id)
    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer','=',True)], default=_default_partner_id)
    reason = fields.Text(string="Reason")
    journal_id = fields.Many2one('account.journal', string="Transfer Journal", required=True)
    memo = fields.Char(string="Memo")
    it_check = fields.Boolean(string="Require IT Check", default=True)
    assign_to = fields.Many2one('hr.employee', string="Assign To")
    type = fields.Selection([
        ('new', 'New'),
        ('borrow', 'Borrow'),
        ('collect_borrow', 'Borrowing Collection'),
    ], string="Transfer Type", required=True, default=_default_type)
    parent_id = fields.Many2one('asset.transfer', 'Agreement')
    collected_date = fields.Date(string="Collected Date", default=_default_collected_date)
    
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
    def _prepare_transfer(self, distribution=None, parent=None):
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
            'line_ids': distribution and self._prepare_transfer_line(distribution) or False,
            'it_check': self.it_check,
            'assign_to': self.assign_to.id,
            'type': self.type,
            'parent_id': parent and parent.id or False,
            'collected_date': self.collected_date,
        }
        return res
    
    @api.multi
    def transfer(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        if self.type in ['new', 'borrow']:
            lines = self.env['asset.distribution.line'].browse(active_ids)
            distribution_ids = [x.distribution_id.id for x in lines]
            distribution_ids = list(set(distribution_ids))
            if len(distribution_ids) > 1:
                raise UserError(_("You can only transfer assets has the same request."))
            vals = self._prepare_transfer(distribution=lines[0].distribution_id)   
        elif self.type == 'collect_borrow':
            lines = self.env['asset.transfer.line'].browse(active_ids)
            transfer_ids = [x.transfer_id.id for x in lines]
            transfer_ids = list(set(transfer_ids))
            if len(transfer_ids) > 1:
                raise UserError(_("You can only collect assets has the same borrowing agreement."))
            vals = self._prepare_transfer(parent=lines[0].transfer_id)
        transfer = self.env['asset.transfer'].create(vals)
        if self.type in ['new', 'borrow']:
            transfer.transfer_confirm()
            lines[0].distribution_id.transfer()
        return {'type': 'ir.actions.act_window_close'}