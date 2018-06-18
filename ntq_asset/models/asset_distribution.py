# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AssetDistribution(models.Model):
    _name = 'asset.distribution'
    _description = 'Asset Distribution'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    @api.one
    @api.depends('distrubute_to', 'employee_id')
    def _compute_approve_status(self):
        if self.distrubute_to == 'project':
            self.approve_status = 'pm'
        elif self.distrubute_to == 'department':
            self.approve_status = 'dm'
        elif self.distrubute_to == 'employee':
            if self.employee_id:
                if self.employee_id.parent_id:
                    self.approve_status = 'em'
                else:
                    if self.employee_id.department_id and self.employee_id.department_id.manager_id:
                        self.approve_status = 'dm'
    
    @api.model
    def default_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee or False
    
    @api.model
    def _default_expired_date(self):
        context = dict(self._context or {})
        default_type = context.get('default_type', False)
        if default_type == 'borrow':
            return fields.Date.today()
        return False
    
    name = fields.Char(string="Title", required=True, readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([
        ('new', 'New'),
        ('borrow', 'Borrow')
    ], string="Distribution Type", required=True)
    distrubute_to = fields.Selection([
        ('employee', 'Employee'),
        ('project', 'Project'),
        ('department', 'Department')
    ], string="Allocate To", required=True, default='employee', readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string="Employee", default=default_employee,
        readonly=True, states={'draft': [('readonly', False)]})
    project_id = fields.Many2one('project.project', string="Project", domain=[('state','in',['draft','open'])], readonly=True, states={'draft': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', string="Department", readonly=True, states={'draft': [('readonly', False)]})
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Priority", required=True, default='medium', readonly=True, states={'draft': [('readonly', False)]})
    distribute_date = fields.Date(string="Request Date", required=True, default=fields.Date.today, readonly=True, states={'draft': [('readonly', False)]})
    deadline = fields.Date(string="Deadline", readonly=True, states={'draft': [('readonly', False)]})
    borrow_date = fields.Date(string="Borrow Date", default=fields.Date.today, readonly=True, states={'draft': [('readonly', False)]})
    expired_date = fields.Date(string="Collected Date", readonly=True, states={'draft': [('readonly', False)]}, default=_default_expired_date)
    asset_group_id = fields.Many2one('asset.group', string="Asset Group", readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(string="Description")
    line_ids = fields.One2many('asset.distribution.line', 'distribution_id', string="Distribution Lines", readonly=True,
        states={
            'draft': [('readonly', False)],
            'waiting': [('readonly', False)],
            'approve': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled'),
        ('approve', 'Approved'),
        ('waiting_avai', 'Waiting Availability'),
        ('available', 'Available'),
        ('transfer', 'Transfered')
    ], string="Status", index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True)
    approve_status = fields.Selection([
        ('pm', 'Approve by PM'),
        ('em', 'Approve by Manager of Employee'),
        ('dm', 'Approve by DM'),
    ], string="Approve Status", compute='_compute_approve_status')
    approve_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    transfer_ids = fields.One2many('asset.transfer', 'distribution_id', string="Transfer")
    
    @api.one
    @api.constrains('borrow_date','expired_date')
    def _check_expired_date(self):        
        if self.expired_date and self.expired_date < self.borrow_date:
            raise UserError(_("Borrow Date must be less than Collected Date."))
        
    @api.one
    @api.constrains('distribute_date','deadline')
    def _check_deadline_date(self):        
        if self.deadline and self.deadline < self.distribute_date:
            raise UserError(_("Request Date must be less than Deadline."))
    
    @api.onchange('asset_group_id','expired_date')
    def onchange_asset_group_id(self):
        if not self.asset_group_id:
            for line in self.line_ids:
                line.expired_date = self.expired_date
        else:
            lines = []
            asset_obj = self.env['product.product']
            for line in self.asset_group_id.line_ids:
                asset = asset_obj.search([
                    ('categ_id','=',line.asset_categ_id.id),
                    ('is_asset','=',True),
                    ('state','in',['draft','new','available'])], limit=1)
                if asset:                
                    lines.append((0, 0, {'asset_id': asset.id, 'name': line.name, 'state': self.state, 'expired_date': self.expired_date}))
                else:
                    lines.append((0, 0, {'name': line.name, 'state':  self.state, 'expired_date': self.expired_date}))
            self.line_ids = lines
            
    @api.onchange('distrubute_to')
    def onchange_distrubute_to(self):
        self.approve_by = False
        if self.distrubute_to == 'employee':
            self.project_id = False
            self.department_id = False
        elif self.distrubute_to == 'project':
            self.employee_id = False
            self.department_id = False
        elif self.distrubute_to == 'department':
            self.employee_id = False
            self.project_id = False
            
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.approve_by = False
        if self.employee_id:
            if self.employee_id.parent_id:
                self.approve_by = self.employee_id.parent_id.user_id or False
            elif self.employee_id.department_id.manager_id:
                self.approve_by = self.employee_id.department_id.manager_id.user_id or False
            
    @api.onchange('project_id')
    def onchange_project_id(self):
        self.approve_by = False        
        if self.project_id:
            self.approve_by = self.project_id.user_id or False
            
    @api.onchange('department_id')
    def onchange_department_id(self):
        self.approve_by = False
        if self.department_id:
            if self.employee_id.department_id.manager_id:
                self.approve_by = self.employee_id.department_id.manager_id.user_id or False                
    
    @api.one
    def submit(self):
        if not self.line_ids:
            raise UserError(_("Please add distribution details before submit!."))
        body = (_("There is an asset distribution need to approve.<br/><ul class=o_timeline_tracking_value_list><li>Title<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (self.name))
        if self.distrubute_to == 'employee':
            if self.employee_id.parent_id:
                if self.employee_id.parent_id.user_id:
                    self.message_post(body=body, partner_ids=[self.employee_id.parent_id.user_id.partner_id.id])
            else:
                if self.employee_id.department_id and self.employee_id.department_id.manager_id:
                    if self.employee_id.department_id.manager_id.user_id:
                        self.message_post(body=body, partner_ids=[self.employee_id.department_id.manager_id.user_id.partner_id.id])   
        elif self.distrubute_to == 'project':
            if self.project_id.user_id:
                self.message_post(body=body, partner_ids=[self.project_id.user_id.partner_id.id])
        elif self.distrubute_to == 'department':
            if self.department_id.manager_id and self.department_id.manager_id.user_id:
                self.message_post(body=body, partner_ids=[self.department_id.manager_id.user_id.partner_id.id])
        self.write({'state': 'waiting'})
        self.sudo().line_ids.write({'state': 'waiting'})
    
    @api.one
    def approve(self):
        is_asset_manager = False
        em_ids = []
        pm_ids = []
        dm_ids = []
        # 20170724-PhuongNT: allow asset manager to have full permission on all function
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('base.group_asset_user'):
            is_asset_manager = True
        body = (_("Asset distribution has approved by Department Manager.<br/><ul class=o_timeline_tracking_value_list><li>Title<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (self.name))
        if self.distrubute_to == 'employee':
            if self.employee_id.parent_id and self.employee_id.parent_id.user_id:
                em_ids.append(self.employee_id.parent_id.user_id.id)
            if self.employee_id.department_id and self.employee_id.department_id.manager_id and self.employee_id.department_id.manager_id.user_id:
                dm_ids.append(self.employee_id.department_id.manager_id.user_id.id)
            
            if (not em_ids and not dm_ids) and is_asset_manager is False:
                    raise UserError(_("You have not enough permission to approve this distribution."))
            else:
                if self.env.user.id not in em_ids and self.env.user.id not in dm_ids and is_asset_manager is False:
                        raise UserError(_("You have not enough permission to approve this distribution."))
        elif self.distrubute_to == 'project':
            body = (_("Asset distribution has approved by Project Manager.<br/><ul class=o_timeline_tracking_value_list><li>Title<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (self.name))
            if self.project_id.user_id:
                pm_ids.append(self.project_id.user_id.id)
                
            if not pm_ids and is_asset_manager is False:
                raise UserError(_("You have not enough permission to approve this distribution."))
            else:
                if self.env.user.id not in pm_ids and is_asset_manager is False:
                    raise UserError(_("You have not enough permission to approve this distribution."))
        elif self.distrubute_to == 'department':
            if self.department_id.manager_id and self.department_id.manager_id.user_id:
                dm_ids.append(self.department_id.manager_id.user_id.id)
                
            if not dm_ids and is_asset_manager is False:
                raise UserError(_("You have not enough permission to approve this distribution."))
            else:
                if self.env.user.id not in dm_ids and is_asset_manager is False:
                    raise UserError(_("You have not enough permission to approve this distribution."))
                        
        self.message_post(body=body, partner_ids=[self.create_uid.partner_id.id])
        self.write({'state': 'approve', 'approve_by': self.env.user.id})
        self.sudo().line_ids.write({'state': 'approve'})
    
    @api.one
    def confirm(self):
        state = 'available'
        po_asset = []
        
        for line in self.line_ids:
            if not line.asset_id:
                raise UserError(_("Please select asset before confirm."))
            else:
                if self.type == 'new':
                    if line.asset_id.state == 'draft':
                        po_asset.append(line.asset_id)
                        state = 'waiting_avai'
                    elif line.asset_id.state == 'new':
                        state = 'waiting_avai'
                        #raise UserError(_("Please set asset '%s' is available.") % line.asset_id.name)                        
                    elif line.asset_id.state != 'available':
                        raise UserError(_("Asset '%s' is not available.") % line.asset_id.name)
                elif self.type == 'borrow':
                    if line.asset_id.state == 'draft':
                        raise UserError(_("Please set asset '%s' is available.") % line.asset_id.name)
                    elif line.asset_id.state == 'new':
                        state = 'waiting_avai'
                    elif line.asset_id.state != 'available':
                        raise UserError(_("Asset '%s' is not available.") % line.asset_id.name)    
                                            
        self.write({'state': state})
        self.line_ids.write({'state': state})
        if state == 'available':
            self.line_ids.set_to_book()
        
    @api.one
    def check_available(self):
        state = 'available'
        
        for line in self.line_ids:
            if line.asset_id.state not in ['available','book']:
                state = 'waiting_avai'
                
        self.write({'state': state})
        self.line_ids.write({'state': state})
        if state == 'available':
            self.line_ids.set_to_book()
        
    @api.one
    def reject(self, reason):
        body = (_("The asset distribution '%s' has been rejected.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (self.name, reason))
        partner_ids = [self.create_uid.partner_id.id]
        if self.state == 'waiting':
            self.message_post(body=body, partner_ids=partner_ids)
        elif self.state == 'approve':
            partner_ids.append(self.approve_by.partner_id.id)
            self.message_post(body=body, partner_ids=partner_ids)
            
        self.write({'state': 'reject'})
        self.sudo().line_ids.write({'state': 'reject'})
        
    @api.one
    def transfer(self):
        self.write({'state': 'transfer'})
        self.line_ids.write({'state': 'transfer'})                  
            
    @api.one
    def cancel(self):
        self.write({'state': 'cancel'})
        self.line_ids.write({'state': 'cancel'})
        self.line_ids.set_to_available()
        
    @api.one
    def set_draft(self):        
        self.write({'state': 'draft'})
        self.line_ids.write({'state': 'draft'})
        
    @api.model
    def _get_approve_by(self, vals):
        employee_id = vals.get('employee_id', False)
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            if employee.parent_id:
                return employee.parent_id.user_id.id or False
            elif employee.department_id.manager_id:
                return employee.department_id.manager_id.user_id.id or False
                
        project_id = vals.get('project_id', False)
        if project_id:
            project = self.env['project.project'].browse(project_id)
            return project.user_id.id or False
            
        department_id = vals.get('department_id', False)
        if department_id:
            department = self.env['hr.department'].browse(department_id)
            if department.manager_id:
                return department.manager_id.user_id.id or False
            
        return False
    
    @api.model
    def create(self, vals):
        vals['approve_by'] = self._get_approve_by(vals)
        result = super(AssetDistribution, self).create(vals)
        return result
    
    @api.multi
    def write(self, vals):
        employee_id = project_id = department_id = False
        distrubute_to = vals.get('distrubute_to', False)
        for r in self:
            if not distrubute_to:
                distrubute_to = r.distrubute_to
        if distrubute_to == 'employee':
            employee_id = vals.get('employee_id', False)
            for r in self:
                if not employee_id:
                    employee_id = r.employee_id.id
        elif distrubute_to == 'project':
            project_id = vals.get('project_id', False)
            for r in self:
                if not project_id:
                    project_id = r.project_id.id
        elif distrubute_to == 'department':
            department_id = vals.get('department_id', False)
            for r in self:
                if not department_id:
                    department_id = r.department_id.id
        vals['employee_id'] = employee_id
        vals['project_id'] = project_id
        vals['department_id'] = department_id
        vals['approve_by'] = self._get_approve_by(vals)            
        result = super(AssetDistribution, self).write(vals)
        return result
    
    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('You can only delete draft distribution!'))
        return super(AssetDistribution, self).unlink()