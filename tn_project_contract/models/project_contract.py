# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError, ValidationError


class ProjectContract(models.Model):
    _name = 'project.contract'
    _description = 'Project Contract'
    _inherit = ['mail.thread']

    name = fields.Char('Name', readonly=True, index=True)
    date = fields.Date('Date', default=fields.date.today())
    payment_percentage = fields.Float(string='Payment Percentage',  copy=False)
    retained_warranty = fields.Float(string='Retained Warenty', copy=False)
    payment_advance = fields.Float(string='Payment Advance', copy=False)
    payment_works = fields.Float(string='Payment Works', copy=False)
    active = fields.Boolean('Active', default=True)
    state = fields.Selection([
         ('draft', 'Draft'),
         ('confirm', 'Confirm')],'State', default="draft")
    total_amount = fields.Float(string='Total', store=True, compute='_compute_total_amount')
    total_invoice = fields.Float(string='Total Invoice', store=True, compute='_compute_request_invoice')
    check_payment = fields.Boolean('Check Payment')
    check_invoice = fields.Boolean('Check Invoice')
    payment_count = fields.Integer(compute="_compute_count_payment", string='payment Count', copy=False)
    invoice_count = fields.Integer(compute="_compute_count_invoice", string='Invoice Count', copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    project_id = fields.Many2one('project.manager',string='Project',required=True)
    analytic_id = fields.Many2one(related='project_id.acc_analytic_id', store=True, string='Analytic Account')
    account_id = fields.Many2one('account.move', 'Account Move')
    invoice_ids = fields.Many2many('account.move', string='Account invoice')
    contract_line_ids = fields.One2many('project.contract.line', 'contract_id', 'Contract Line')

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('project.contract.seq')
        vals.update({
            'name': seq
            })
        res = super(ProjectContract, self).create(vals)
        return res


    def unlink(self):
        for rec in self:
            if rec.state == 'confirm':
                raise UserError(_('You can only delete project contract in draft.'))
        return super(ProjectContract, self).unlink()

    # def unlink(self):
    #     


    def make_confirm(self):
        self.state = 'confirm'

    @api.depends('contract_line_ids.price')
    def _compute_total_amount(self): 
        total = 0.0 
        for line in self.contract_line_ids:                 
            total+= line.price    
        self.total_amount = total

    @api.depends('contract_line_ids.invoice_request')
    def _compute_request_invoice(self): 
        total = 0.0 
        for line in self.contract_line_ids:                 
            total+= line.invoice_request    
        self.total_invoice = total

    @api.depends('account_id')
    def _compute_count_payment(self):
        for acc in self:
            acc.payment_count = len(acc.account_id)

    @api.depends('invoice_ids')
    def _compute_count_invoice(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.onchange('payment_percentage', 'total_amount')
    def _onchange_payment_advance(self):
        for rec in self:
            if rec.payment_percentage:
                rec.payment_advance = (rec.total_amount*rec.payment_percentage) / 100 

    @api.onchange('payment_percentage', 'total_invoice')
    def _onchange_payment_works(self):
        for rec in self:
            if rec.payment_percentage:
                rec.payment_works = (rec.total_invoice*rec.payment_percentage) / 100 

    def _get_invoiced(self):
        for rec in self:
            for line in rec.contract_line_ids:
                if line.invoice_request:
                    line.invoiced+= line.invoice_request

    def check_payment_percentage(self):
        for rec in self:
            if rec.payment_percentage == 0:
                raise UserError(_('payment advance percentage should not equal 0'))


    def check_invoice_request(self):
        for rec in self:
            if all(
                line.invoice_request == 0
                for line in rec.contract_line_ids
            ):
              raise UserError(_('Enter value in invoice request '))


    def create_payment_invoice(self):
        if not self.contract_line_ids:
             raise UserError(_(' You cannot create payment invoice  because there is no Division line.'))
        self.check_payment_percentage()
        self.check_payment = True
        line_vals = self._prepare_invoice_line()
        lst_vals = {
            'move_type': 'out_invoice',
            'invoice_date': fields.date.today(),
            'partner_id': self.partner_id.id,
            'advance_pay': self.payment_advance,
            'is_pay': True,
            'project_contract_id': self.id,
            'invoice_line_ids': line_vals,
        }
        move_id = self.env['account.move'].create(lst_vals)
        self.account_id = move_id.id

    def create_invoice(self):
        self.check_invoice_request()
        self.check_invoice = True
        self.check_payment = False
        self._get_invoiced()
        obj_move = self.env['account.move']
        move_ids = []
        line_vals = self._prepare_invoice_line()
        
        lst_vals = {
            'move_type': 'out_invoice',
            'invoice_date': fields.date.today(),
            'partner_id': self.partner_id.id,
            'advance_pay': self.payment_advance,
            'amount_works': self.total_invoice,
            'project_contract_id': self.id,
            'check_invoice': True,
            'invoice_line_ids': line_vals,
        }
        move_id = self.env['account.move'].create(lst_vals)
        for move in obj_move.search([('project_contract_id', '=', self.id), ('check_invoice', '=', True)]):
            move_ids.append(move.id)
        self.invoice_ids = [(6, 0, move_ids)]

    def _prepare_invoice_line(self):
        product_works = self.env['ir.config_parameter'].sudo().get_param('tn_project_contract.product_works_id') or False
        product_payment = self.env['ir.config_parameter'].sudo().get_param('tn_project_contract.product_adv_pay_id') or False
        product_retain =  self.env['ir.config_parameter'].sudo().get_param('tn_project_contract.product_retain_warranty_id') or False
        product_obj = self.env['product.product']
        tax_id = self.env['account.tax'].browse(1)
        advance_payment = 0
        price_works = 0
        price_unit_retained = 0
        price_unit_payment = 0
        count = 0
        lst = []
        dict_line = []
        
        if self.check_payment == True:
            advance_payment+= self.payment_advance
            lst.append(product_payment)

        if self.check_invoice == True:
            price_works+= self.total_invoice
            price_unit_payment+= self.payment_works
            price_unit_retained+= (price_works*self.retained_warranty) / 100
            lst.append(product_works)
            lst.append(product_payment)
            lst.append(product_retain)

        for line in lst:
            product_id = product_obj.browse(int(line))
            account_id = product_id.property_account_expense_id
            count+= 1

            if not tax_id:
                raise UserError(_('No Taxs defined, create new tax from account tax'))
            if not product_id:
                raise UserError(_('No product defined check product in project contract setting'))
            if not account_id:
                raise UserError(_('No account defined for product "%s".', product_id.name))

            invoice_line_vals = {
                'product_id': product_id.id,
                'name': self.name + ' '+ self.project_id.name,
                'account_id': account_id.id,
                'analytic_account_id': self.analytic_id.id,
                'tax_ids':  [(6, 0, tax_id.ids)],
                'price_unit': advance_payment,
                            }
            if self.check_invoice == True:
                if count == 1:
                    invoice_line_vals.update({
                        'price_unit': price_works,
                    })
                if count == 2:
                    invoice_line_vals.update({
                        'price_unit': -price_unit_payment,  
                    })
                if count == 3:
                    invoice_line_vals.update({
                        'price_unit': -price_unit_retained, 
                        'tax_ids': False 
                    })
            dict_line.append((0, 0, invoice_line_vals))
        return dict_line

    def action_show_invoice_payment(self):
        for rec in self:
            account_move_invoice = self.env.ref('account.action_move_out_invoice_type')
            account_payment_invoice = account_move_invoice.read()[0]
            account_payment_invoice['domain'] = str([('project_contract_id','=',rec.id), ('is_pay', '=', True)])
        return account_payment_invoice

    def action_show_works_invoice(self):
        for rec in self:
            account_move_invoice = self.env.ref('account.action_move_out_invoice_type')
            account_work_invoice = account_move_invoice.read()[0]
            account_work_invoice['domain'] = str([('project_contract_id','=',rec.id), ('check_invoice', '=', True)])
        return account_work_invoice

    


class ProjectContractLine(models.Model):
    _name = 'project.contract.line'
    _description = 'Project Contract Line'

    contract_id = fields.Many2one('project.contract', string='Reference Project Contract', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Char(string='description')
    price = fields.Float('Price')
    invoice_request = fields.Float('Invoice Request')
    invoiced = fields.Float('Invoiced')
    remaining = fields.Float('remaining of Price', compute='_compute_price_rimaining', store=True)


    @api.depends('price', 'invoice_request', 'invoiced')
    def _compute_price_rimaining(self): 
        for line in self:
            if line.price:
                line.remaining = line.price - line.invoiced
            if line.price < 0 or line.invoice_request < 0:
                raise ValidationError("Number should not be less than zero")
            # if  line.invoice_request > line.price:
            #     raise ValidationError("Invoice Request  greater than price")

   

    

        
   