# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AssetTransfer(models.Model):
    _name = 'asset.transfer'
    _description = 'Asset Transfer'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    @api.model
    def _default_transfer_by(self):
        context = dict(self._context or {})
        default_type = context.get('default_type', False)
        employee = False
        if default_type in ['new','borrow']:
            employee = self.env['hr.employee'].search([('user_id','=', self.env.user.id)], limit=1)
        return employee
    
    @api.model
    def _default_retrieve_by(self):
        context = dict(self._context or {})
        default_type = context.get('default_type', False)
        employee = False
        if default_type in ['collect_new','collect_borrow']:
            employee = self.env['hr.employee'].search([('user_id','=', self.env.user.id)], limit=1)
        return employee
    
    name = fields.Char(string="Reference", required=True, readonly=True, default='/')
    date = fields.Date(string="Ngày Cấp Phát", required=True, default=fields.Date.today, readonly=True, states={'draft': [('readonly', False)]})
    transfer_by = fields.Many2one('hr.employee', string="Người cấp phát", required=True, default=_default_transfer_by,
        readonly=True, states={'draft': [('readonly', False)]}, auto_join=True)
    retrieve_by = fields.Many2one('hr.employee', string="Người nhận", required=True, default=_default_retrieve_by,
        readonly=True, states={'draft': [('readonly', False)]}, auto_join=True)
    own_by = fields.Selection([
        ('employee', 'Người Dùng'),
        ('project', 'Dự án'),
        ('department', 'Phòng Ban'),
        ('customer', 'Nhân Viên'),
    ], string="Used By", readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string="Nhân Viên", readonly=True, states={'draft': [('readonly', False)]})
    project_id = fields.Many2one('project.project', string="Dự Án", readonly=True, states={'draft': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', string="Phòng Ban", readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer','=',True)], readonly=True, states={'draft': [('readonly', False)]})
    distribution_id = fields.Many2one('asset.distribution', string="Request", readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', string="Transfer Journal", readonly=True, states={'draft': [('readonly', False)]})
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    memo = fields.Char(string="Memo", readonly=True, states={'draft': [('readonly', False)]})
    reason = fields.Text(string="Reason", readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('transfer_confirm', 'Confirmed by Transfer'),
        ('it_confirm', 'Confirmed'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled'),
    ], index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True)
    line_ids = fields.One2many('asset.transfer.line', 'transfer_id', string="Transfer Asset", readonly=True, states={'draft': [('readonly', False)]})
    it_check = fields.Boolean(string="Require IT Check", default=True, readonly=True, states={'draft': [('readonly', False)]})
    assign_to = fields.Many2one('hr.employee', string="Assign To", readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([
        ('new', 'Allocate New'),
        ('borrow', 'Allocation Borrowing'),
        ('collect_new', 'Allocation Collection'),
        ('collect_borrow', 'Borrowing Collection'),    
    ], string="Transfer Type", required=True)
    parent_id = fields.Many2one('asset.transfer', 'Agreement', readonly=True, states={'draft': [('readonly', False)]})
    child_ids = fields.One2many('asset.transfer', 'parent_id', string="Child")
    collected_count = fields.Integer(string="# of Collecting", compute='_count_collected')
    collected = fields.Boolean(string="Collected")
    collected_date = fields.Date(string="Collected Date", readonly=True, states={'draft': [('readonly', False)]})
    
    @api.depends('child_ids')
    def _count_collected(self):
        for r in self:
            r.collected_count = len(r.child_ids)
    
    @api.onchange('retrieve_by')
    def onchange_retrieve_by(self):
        self.department_id = self.retrieve_by.department_id.id or False
        
    @api.onchange('it_check')
    def onchange_it_check(self):
        if self.it_check:
            model_data = self.env['ir.model.data']
            it_group_id = model_data.xmlid_to_res_id('base.group_asset_it', raise_if_not_found=True)
            it_group = self.env['res.groups'].browse(it_group_id)
            user_ids = [x.id for x in it_group.users]
            return {'domain': {'assign_to': [('user_id','in',user_ids)]}}
        else:
            self.assign_to = False
    
    @api.onchange('transfer_by')
    def onchange_transfer_by(self):
        if self.type == 'collect_new':
            if self.transfer_by:
                asset_transfer_by = self.search([('retrieve_by','=',self.transfer_by.id), 
                                                 ('state', '=', 'done'), ('type', '=', 'new')], limit= 1, order='name desc')
#                 if asset_transfer_by:
                self.parent_id= asset_transfer_by.id
        elif self.type == 'collect_borrow':
            if self.transfer_by:
                asset_transfer_by = self.search([('retrieve_by','=',self.transfer_by.id), 
                                                 ('state', '=', 'done'), ('type', '=', 'borrow')], limit=1, order='name desc')
#                 if asset_transfer_by:
                self.parent_id= asset_transfer_by.id      
                
    @api.onchange('own_by')
    def onchange_own_by(self):
        if self.own_by == 'employee':
            self.project_id = False
            self.department_id = False
            self.partner_id = False
        elif self.own_by == 'project':
            self.employee_id = False
            self.department_id = False
            self.partner_id = False
        elif self.own_by == 'department':
            self.employee_id = False
            self.project_id = False
            self.partner_id = False
        elif self.own_by == 'customer':
            self.employee_id = False
            self.project_id = False
            self.department_id = False
    
    @api.onchange('distribution_id')
    def onchange_distribution_id(self):
        lines = []
        for line in self.distribution_id.line_ids:
            lines.append((0, 0, {
                'asset_id': line.asset_id.id,
                'description': line.name,
                'distribution_id': self.distribution_id.id,
                'state': 'draft',
            }))
            
        if self.distribution_id:
            self.own_by = self.distribution_id.distrubute_to
            self.employee_id = self.distribution_id.employee_id.id
            self.project_id = self.distribution_id.project_id.id
            self.department_id = self.distribution_id.department_id.id
            self.collected_date = self.distribution_id.expired_date
        self.line_ids = lines
        
    @api.onchange('parent_id')
    def onchange_parent_id(self):
        lines = []
        for line in self.parent_id.line_ids:
            lines.append((0, 0, {
                'asset_id': line.asset_id.id,
                'asset_code': line.asset_code,
                'description': line.name,
                'state': 'draft',
            }))
            
        if self.parent_id:
            self.own_by = self.parent_id.own_by
            self.employee_id = self.parent_id.employee_id.id
            self.project_id = self.parent_id.project_id.id
            self.department_id = self.parent_id.department_id.id
        self.line_ids = lines
        
    @api.one
    def _send_notification(self, notification_type, reason=None):
        if notification_type == 'confirm':
            body = (_("The transfer '%s' has been confirmed by '%s'.") % (self.name, self.env.user.name))
        elif notification_type == 'reject':
            if not reason:
                raise UserError(_("You must enter reason."))
            body = (_("The transfer '%s' has been rejected by '%s'.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (self.name, self.env.user.name, reason))
        elif notification_type == 'done':
            body = (_("The transfer '%s' has been done by '%s'.") % (self.name, self.env.user.name))
        elif notification_type == 'cancel':
            body = (_("The transfer '%s' has been canceled by '%s'.") % (self.name, self.env.user.name))
            
        partner_ids = []
        if self.transfer_by.user_id:
            partner_ids.append(self.transfer_by.user_id.partner_id.id)
        if self.retrieve_by.user_id:
            partner_ids.append(self.retrieve_by.user_id.partner_id.id)
        if self.it_check and self.assign_to.user_id:
            partner_ids.append(self.assign_to.user_id.partner_id.id)
            
        self.message_post(body=body, partner_ids=partner_ids)                        
    
    @api.one
    def transfer_confirm(self):
        is_asset_manager = False
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('base.group_asset_user'):
            is_asset_manager = True
        if not self.line_ids:
            raise UserError(_("Please create some transfer asset."))
        for line in self.line_ids:
            if self.type in ['new','borrow']:
                if line.asset_id.state not in ['book','available']:
                    raise UserError(_("Asset '%s' must be Available.") % line.asset_id.name)
            if self.type in ['collect_new','collect_borrow']:
                if line.asset_id.state not in ['use']:
                    raise UserError(_("Asset '%s' must be In Use") % line.asset_id.name)
#             if self.type in ['new','borrow']:
#                 if line.asset_id.state not in ['book','available']:
#                     raise UserError(_("You cannot transfer asset '%s'. Because it's status is not book or available.") % line.asset_id.name)
#             if self.type in ['collect_new','collect_new']:
#                 if line.asset_id.state not in ['use']:
#                     raise UserError(_("You cannot transfer asset '%s'. Because it's status is not in use.") % line.asset_id.name)
        if (not self.transfer_by.user_id or self.transfer_by.user_id.id != self.env.user.id) and is_asset_manager is False:
            raise UserError(_("You have not enough permission to confirm this transfer."))
        self.write({'state': 'transfer_confirm'})
        self._send_notification(notification_type='confirm')
    
    @api.one
    def it_confirm(self):
        # if self.it_check:
        #     if not self.assign_to.user_id or self.assign_to.user_id.id != self.env.user.id:
        #         raise UserError(_("You have not enough permission to confirm this transfer."))
        self.write({'state': 'it_confirm'})
        self._send_notification(notification_type='confirm')
        
    @api.one
    def reject(self, reason):
        # if self.it_check:
        #     if not self.assign_to.user_id or self.assign_to.user_id.id != self.env.user.id:
        #         raise UserError(_("You have not enough permission to reject this transfer."))
        self.write({'state': 'reject'})
        self._send_notification(notification_type='reject', reason=reason)
        self.line_ids.sudo().reject()
        
    @api.one
    def done(self):
        is_asset_manager = False
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('base.group_asset_user'):
            is_asset_manager = True
        if not self.transfer_by.user_id:
            raise UserError(_("Please set Related User for Transfer By '%s'.") % self.transfer_by.name)
        if (not self.retrieve_by.user_id or self.retrieve_by.user_id.id != self.env.user.id) and is_asset_manager is False:
                raise UserError(_("You have not enough permission to done this transfer."))
            
        self.write({'state': 'done'})
        
        if self.type in ['new', 'borrow']:
            self.line_ids.done()
            
            if self.state == 'done':
                asset_obj = self.env['product.template']
                for r in self.line_ids:
                    asset_obj.browse(r.asset_code.id).sudo().write({
                        'own_by': r.own_by,
                        'employee_id': r.employee_id.id or False,
                        'project_id': r.project_id.id or False,
                        'department_id': r.department_id.id or False,
                        'partner_id': r.partner_id.id or False,})
            if self.distribution_id and self.distribution_id.state == 'available':
                self.distribution_id.transfer()
                
        if self.type in ['collect_new', 'collect_borrow']:
            self.line_ids.done()
            if self.parent_id:
                self.parent_id.write({'collected': True})
                self.parent_id.line_ids.collect()
            
        self._send_notification(notification_type='done')
    
    @api.model
    def _prepare_move_line(self, transfer_line):
        partner_id = self.retrieve_by.address_home_id.id or False
        res = []
        debit = 0
        for line in transfer_line:
            if not line.asset_id.categ_id.property_stock_valuation_account_id:
                raise UserError(_("You must define stock valuation account on asset category '%s'.") % line.asset_id.categ_id.name)
                                            
            debit += line.asset_id.value
            # credit journal item
            res.append((0, 0, {
                'date_maturity': self.date,
                'partner_id': partner_id,
                'name': self.memo or self.name,
                'debit': 0,
                'credit': line.asset_id.value,
                'account_id': line.asset_id.categ_id.property_stock_valuation_account_id.id,
                'ref': self.memo or self.name,
                'quantity': 1,
            }))
            
        # debit journal item
        res.append((0, 0, {
            'date_maturity': self.date,
            'partner_id': partner_id,
            'name': self.memo or self.name,
            'debit': debit,
            'credit': 0,
            'account_id': self.journal_id.default_debit_account_id.id,
            'ref': self.memo or self.name,
            'quantity': 1,
        }))
            
        return res
    
    @api.model
    def _prepare_move(self, transfer_line):
        if not self.journal_id.default_debit_account_id:
            raise UserError(_("You must define default debit account on journal '%s'.") % self.journal_id.name)            
        res = {
            'journal_id': self.journal_id.id,
            'company_id': self.env.user.company_id.id,
            'date': self.date,
            'ref': self.memo or self.name,
            'line_ids': self._prepare_move_line(transfer_line),
        }
        return res
    
    @api.one
    def create_move(self):
        if not self.journal_id:
            raise UserError(_("Please select Transfer Journal."))
        vals = self.sudo()._prepare_move(self.line_ids)
        move = self.env['account.move'].sudo().create(vals)
        move.sudo().post()
        self.write({'move_id': move.id})
    
    @api.one
    def cancel_move(self):
        if self.move_id:
            if self.move_id.state == 'draft':
                self.move_id.sudo().unlink()
            else:
                self.move_id.sudo().button_cancel()
                self.move_id.sudo().unlink()
    
    @api.one
    def cancel(self):
        if self.type in ['new','borrow']:
            if self.distribution_id:
                self.distribution_id.write({'state': 'available'})
                self.distribution_id.line_ids.write({'state': 'available'})
        if self.type in ['collect_new','collect_new']:
            if self.parent_id:
                self.parent_id.write({'collected': False})
                self.parent_id.line_ids.cancel()
        
        self.write({'state': 'cancel'})
        self.line_ids.cancel()
        self._send_notification(notification_type='cancel')
        
    @api.one
    def set_draft(self):
        self.write({'state': 'draft'})
        self.line_ids.draft()        
    
    @api.model
    def create(self, vals):
        lines = []
        distribution_id = vals.get('distribution_id', False)
        parent_id = vals.get('parent_id', False)
        if distribution_id:
            distribution = self.env['asset.distribution'].browse(distribution_id)
            for line in distribution.line_ids:
                lines.append((0, 0, {
                    'asset_code': line.asset_id.id,
                    'child_id': [(6, 0, [x.id for x in line.child_id])],
                    'description': line.name,
                    'distribution_id': self.distribution_id.id,
                    'state': 'draft',
                }))
            vals['line_ids'] = lines
        if parent_id:
            parent = self.env['asset.transfer'].browse(parent_id)
            for line in parent.line_ids:
                lines.append((0, 0, {
                    'asset_id': line.asset_id.id,
                    'asset_code': line.asset_code.id,
                    'child_id': [(6, 0, [x.id for x in line.child_id])],
                    'description': line.name,
                    'state': 'draft',
                }))
            vals['line_ids'] = lines        
        
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('asset.transfer') or '/'
        result = super(AssetTransfer, self).create(vals)
        return result
    
    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('You can only delete draft transfer!'))        
        return super(AssetTransfer, self).unlink()