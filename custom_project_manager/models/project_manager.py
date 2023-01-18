
from odoo import models, fields, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import  ValidationError
from odoo.exceptions import  UserError


class ProjectManager(models.Model):
    _name = 'project.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Project Manager'


    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete Project Manager which is not in draft or cancelled state.'))
        return super(ProjectManager, self).unlink()

    name = fields.Char(
        string='Name', 
        required=True
    )
    code = fields.Char(
        string='Short Name', 
        required=True,
        size=5,
    )
    state = fields.Selection([
        ('draft', 'New'),
        ('supmit', 'Confirm'),
        ('confirm', 'Done'),
        ('cancel', 'Canceled')],
        default='draft',
        tracking=True,
    )
    date_from = fields.Datetime(
        string='Date From', 
        required=True
    )
    date_to = fields.Datetime(
        string='Date To', 
        required=True
    )
    emp_id = fields.Many2one(
        'hr.employee',
        string='Project Manager', 
        required=True
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warhouse',
        readonly=True
    )
    acc_analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        readonly=True, 
    )

    

   
    @api.constrains('date_to', 'date_from')
    def date_constrains(self):
    	for rec in self:
    		if rec.date_to < rec.date_from:
    		 raise ValidationError(_('Sorry, Date To Must be greater Than Date From...'))
    	

    def set_supmit(self):
    	for rec in self:
    		rec.state = 'supmit'

    def set_confirm_project(self):
    	for rec in self:
            lst = {
                'name': rec.name,
                'company_id': rec.emp_id.company_id.id
            }
            pic_vals = {
                'name': rec.name,
                'code': rec.code
            }
            analytic_account = self.env['account.analytic.account'].create(lst)
            warehouse = self.env['stock.warehouse'].create(pic_vals)
            if rec.name == rec.acc_analytic_id.name and rec.name == rec.warehouse_id.name:
               pass
            else:
                rec.acc_analytic_id = analytic_account.id
                rec.warehouse_id = warehouse.id
            rec.state = 'confirm'

    def set_cancel(self):
    	for rec in self:
    		rec.state = 'cancel'

 