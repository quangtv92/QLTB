# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class Asset(models.Model):
    _inherit = 'product.template'
    
    def _get_default_category_id(self):
        context = dict(self._context or {})
        is_asset = context.get('default_is_asset', False)
        if not is_asset:
            return super(Asset, self)._get_default_category_id()
        return False
    
    def _get_default_uom_id(self):
        return self.env.ref('product.product_uom_day', False).id

    is_asset = fields.Boolean(string="Can be Asset")
    purchase_ok = fields.Boolean('Can be Purchased', default=True)
    asset_code = fields.Char(string='Code', required=False, index=True)
    serial = fields.Char(string="Serial", readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(string="Description")
    label = fields.Char(string="Label Name")
    warranty_from = fields.Date(string="Warranty From", readonly=True, states={'draft': [('readonly', False)]})
    warranty_to = fields.Date(string="Warranty To", readonly=True, states={'draft': [('readonly', False)]})
    warranty_reference = fields.Char(string="Warranty Reference")
    own_by = fields.Selection([
        ('employee', 'Employee'),
        ('project', 'Project'),
        ('department', 'Department'),
        ('company', 'Company'),
        ('customer', 'Customer'),
    ], string="Own By", readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True, states={'draft': [('readonly', False)]})
    project_id = fields.Many2one('project.project', string="Project", readonly=True, states={'draft': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', string="Department", readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer','=',True)], readonly=True, states={'draft': [('readonly', False)]})
    origin = fields.Selection([
        ('buy', 'Buy'),
        ('gift', 'Gift'),
        ('rent', 'Rent'),
        ('borrow', 'Borrow'),
    ], sring="Origin", readonly=True, states={'draft': [('readonly', False)]})
    origin_partner_id = fields.Many2one('res.partner', string="Partner", readonly=True, states={'draft': [('readonly', False)]})
    origin_date = fields.Date(string="Date", readonly=True, states={'draft': [('readonly', False)]})
    give_account_move_id = fields.Many2one('account.move', string="Gift Journal Entry", readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order", domain=[('state','=','purchase')],
        readonly=True, states={'draft': [('readonly', False)]})
    purchase_date = fields.Date(string="Purchase Date", readonly=True, states={'draft': [('readonly', False)]})
    request_by = fields.Many2one('hr.employee', string="Request By", readonly=True, states={'draft': [('readonly', False)]})
    request_date = fields.Date(string="Request Date", readonly=True, states={'draft': [('readonly', False)]})
    approve_request_by = fields.Many2one('hr.employee', string="Approve By", readonly=True, states={'draft': [('readonly', False)]})
    available_date = fields.Date(string="Available Date", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    value = fields.Float(string="Value", required=True, default=0, digits=(16,0))
    account_asset_id = fields.Many2one('account.asset.asset', string="Accounting Asset")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('new', 'New'),
        ('available', 'Available'),
        ('book', 'Booked'),
        ('use', 'In Use'),
        ('fail', 'Fail'),        
        ('repair', 'Repair'),
        ('lost', 'Lost'),
        ('liquidated', 'Liquidated'),
        ('disposed', 'Disposed'),
        ('cancel', 'Canceled')
    ], string="Status", index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True)
    categ_id = fields.Many2one('product.category','Internal Category', required=True, change_default=True, domain="[('type','=','normal')]",
        default=_get_default_category_id,help="Select category for the current product")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    history_ids = fields.One2many('asset.history', 'asset_id', string="History", readonly=True)
    parent_id = fields.Many2one('product.template', string="Parent", ondelete='cascade', domain=[('state','in',['new','available'])],
        readonly=True, states={'draft': [('readonly', False)], 'new': [('readonly', False)], 'available': [('readonly', False)]})
    child_id = fields.One2many('product.template', 'parent_id', string="Child Assets")
    parent_left = fields.Integer(string="Left Parent")
    parent_right = fields.Integer(string="Right Parent")
    last_used = fields.Many2one('hr.employee', compute="_compute_last_used", store=True)
    sale_ok = fields.Boolean(
        'Can be Sold', default=False,
        help="Specify if the product can be selected in a sales order line.")
    purchase_ok = fields.Boolean('Can be Purchased', default=False)
    uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default Unit of Measure used for all stock operation.")
    uom_po_id = fields.Many2one(
        'product.uom', 'Purchase Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default Unit of Measure used for purchase orders. It must be in the same category than the default unit of measure.")
    type = fields.Selection([
        ('consu', _('Consumable')),
        ('service', _('Service')),
        ('product', 'Stockable Product'),], string='Product Type', default='product', required=True,
        help='A stockable product is a product for which you manage stock. The "Inventory" app has to be installed.\n'
             'A consumable product, on the other hand, is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.\n'
             'A digital content is a non-material product you sell online. The files attached to the products are the one that are sold on '
             'the e-commerce such as e-books, music, pictures,... The "Digital Product" module has to be installed.')

    # @api.multi
    # def name_get(self, context=None):
    #     if context is None:
    #         context={'test nha'}
    #     res = []
    #     for record in self:
    #         if record.asset_code:
    #             name = record.asset_code + " /" + record.name
    #             res.append((record.id, name))
    #         return res

    @api.multi
    def name_get(self, context={'show_asset_code': False}):
        if not self._context.get('show_asset_code', True):
            return super(Asset, self).name_get()
        return [(value.id, "%s" % (value.asset_code)) for value in self]
    
    
    @api.one
    @api.depends('employee_id') #'history_ids'
    def _compute_last_used(self):
#         last_used = self.env['asset.history'].search([('asset_id','=',self.id)], limit=1, order='date desc').retrieve_by
#         if not last_used:
#             last_used = self.env['product.template'].browse().employee_id
        last_used = self.employee_id.id
        self.last_used = last_used
    
    @api.one
    @api.constrains('warranty_from', 'warranty_to')
    def _check_date_constrains(self):
        if self.warranty_from > self.warranty_to:
            raise ValidationError(_("Warranty To must be greater than Warranty From!."))

    @api.one
    @api.constrains('asset_code')
    def _check_asset_code_constrains(self):
        asset_obj = self.env['product.template']
        duplicated_code = asset_obj.search([('asset_code', '=', self.asset_code)])
        if len(duplicated_code) > 1:
            raise ValidationError(_("Asset code must be unique!."))

    @api.onchange('purchase_order_id')
    def onchange_purchase_order(self):
        self.purchase_date = self.purchase_order_id.date_order

    @api.onchange('categ_id')
    def onchange_category(self):
        if self.categ_id:
            if self.categ_id.code:
                asset_code = self.categ_id.code.next_by_id()
            else:
                asset_code = '/'
            self.asset_code = asset_code
            
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive assets.'))
        return True
    
    @api.one
    def new_asset(self):
        self.write({'state':'new'})
        self.child_id.write({'state':'new'})
        
    @api.one
    def available_asset(self):
        self.write({'state':'available', 'available_date':fields.Date.context_today(self)})
        self.child_id.write({'state':'available', 'available_date':fields.Date.context_today(self)})
        
    @api.one
    def book_asset(self):
        self.write({'state': 'book'})
        self.child_id.write({'state': 'book'})
    
    @api.one
    def use_asset(self):
        self.write({'state':'use'})
        self.child_id.write({'state': 'use'})
        if self.parent_id:
            self.parent_id = False
            
    @api.one
    def repair_asset(self):
        self.write({'state':'repair'})
        
    @api.one
    def fail_asset(self):
        self.write({'state':'fail'})
        self.child_id.write({'state':'fail'})
    
    @api.one
    def lost_asset(self, reason, lost_date, responsible):
        body = (_("The asset '%s' has been lost.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li><li>Lost Date<span> : </span><span class=o_timeline_tracking_value>%s</span></li><li>Responsible<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>")
                % (self.name, reason, lost_date, responsible.name))                              
        self.message_post(body=body, partner_ids=[])
        self.write({'state':'lost'})
        self.child_id.write({'state': 'lost'})
        
    @api.one
    def liquidate_asset(self, reason, liquidated_date, responsible):
        body = (_("The asset '%s' has been liquidated.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li><li>Liquidated Date<span> : </span><span class=o_timeline_tracking_value>%s</span></li><li>Responsible<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>")
                % (self.name, reason, liquidated_date, responsible.name))                              
        self.message_post(body=body, partner_ids=[])
        self.write({'state':'liquidated'})
        self.child_id.write({'state': 'liquidated'})
        
    @api.one
    def dispose_asset(self, reason, disposed_date):
        body = (_("The asset '%s' has been disposed.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li><li>Disposed Date<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>")
                % (self.name, reason, disposed_date))                              
        self.message_post(body=body, partner_ids=[])
        self.write({'state':'disposed'})
        self.child_id.write({'state': 'disposed'})
        
    @api.one
    def generate_entry(self, move):
        self.write({'give_account_move_id': move.id})
        
    @api.one
    def cancel_gift_entry(self):
        if self.give_account_move_id:
            if self.give_account_move_id.state == 'draft':
                self.give_account_move_id.unlink()
            else:
                self.give_account_move_id.button_cancel()
                self.give_account_move_id.unlink()
    
    @api.one
    def cancel_asset(self):
        self.write({'state':'cancel'})
        
    @api.one
    def draft_asset(self):
        self.write({'state':'draft'})
        
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=200):
        res = super(Asset, self).name_search(name, args=args, operator=operator, limit=limit)
        domain = []
        if not res:
            if name:
                domain = ['|', ('name', operator, name), ('asset_code', operator, name)]
                res = self.search(domain, limit=limit)
        return res
        
    @api.model
    def create(self, vals):
        if vals['is_asset'] == False:
            vals['asset_code'] = ""
        res = super(Asset, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'is_asset' in vals and vals['is_asset'] == False:
            vals['asset_code'] = ""
        res = super(Asset, self).write(vals)
        return res