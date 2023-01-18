# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import  ValidationError
from odoo.exceptions import  UserError


class MaterialPurchaseRequisition(models.Model):
    _inherit = 'material.purchase.requisition'

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Confirm project manager'),
        ('project', 'Direct of Project Management'),
        ('technical', 'Store Manager'),
        ('store', 'Supply Chain'),
        ('supply_done', 'Done'),
        ('supply_chain', 'Procurement & contract manager'),
        ('procurement', 'Supply chain manager'),
        ('supply_manager', 'Cost control manager'),
        ('cost_control', 'CEO Approved'),
        ('ceo_approve', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Canceled')],
        default='draft',
        tracking=True,
    )
    

    delivery_type_id = fields.Many2one(
        'stock.picking.type',
        string='Delivery',
        copy=False,
    )
    recipt_type_id = fields.Many2one(
        'stock.picking.type',
        string='Recipt',
        copy=False,
    )
    check_po= fields.Boolean(
        string='Check Qty Remaining',
    )
    price_total = fields.Float(
        compute='_compute_total_amount',
        string='Total'
    )
    check_price= fields.Boolean(
        string='Check Price',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner'
    )
    project_id = fields.Many2one(
        'project.manager',
        string='Project',
    )
    

    @api.onchange('project_id')
    def _onchange_project(self):
        wh_main = self.env['stock.warehouse'].search([('out_type_id.default_location_src_id.main_location', '=',True)])
        for rec in self:
            rec.analytic_account_id = rec.project_id.acc_analytic_id.id
            rec.recipt_type_id = rec.project_id.warehouse_id.in_type_id.id
            rec.delivery_type_id = wh_main.out_type_id.id


    @api.depends('requisition_line_ids.sub_total')
    def _compute_total_amount(self):  
        for rec in self:      
            total = 0.0       
            for line in rec.requisition_line_ids:      
                 total += line.sub_total    
            rec.update({'price_total': total })

    # @api.model
    # def _get_picking_type_delivery(self, company_id):
    #     picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)])
    #     if not picking_type:
    #         picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', False)])
    #     return picking_type[:1]

    
    def set_submit(self):
        for rec in self:
            if not rec.requisition_line_ids:
                raise UserError(_('Please create some requisition lines.'))
            rec.check_po = False
            rec.check_price = False
            rec.state = 'submit'

    def set_project_manager(self):
    	for rec in self:
    		rec.state = 'project'

    def set_store_manager(self):
        for rec in self:
            rec.state = 'store'

    def set_technical_office(self):
    	for rec in self:
            for line in rec.requisition_line_ids:
                if line.qty_po !=0:
                    rec.check_po = True
            rec.state = 'technical'

    def set_supply_chain(self):
    	for rec in self:
            if any(line.check_po == True for line in rec.requisition_line_ids):
                rec.check_po =True
            if all(line.qty_pick == 0 for line in rec.requisition_line_ids):
                pass
            else:
                rec.request_stock_picking()
            rec.state = 'supply_chain'

    def set_supply_chain_done(self):
        for rec in self:
            if any(line.check_po == True for line in rec.requisition_line_ids):
                rec.check_po =True
            if all(line.qty_pick == 0 for line in rec.requisition_line_ids):
                pass
            else:
                rec.request_stock_picking()
            rec.state = 'supply_done'

    def set_procurement_contract(self):
    	for rec in self:
            if rec.price_total <= 3000:
                rec.check_price = True
                rec.state = 'done'
                rec.request_purchase_requisition()
            else:
                rec.state = 'procurement'

    def set_supply_chain_manager(self):
    	for rec in self:
            if rec.price_total > 3000 and rec.price_total < 20000:
                rec.check_price = True
                rec.state = 'done'
                rec.request_purchase_requisition()
            else:
                rec.state = 'supply_manager'

    def set_cost_control(self):
    	for rec in self:
            if rec.price_total > 20000:
                rec.check_price = True
                rec.state = 'done'
                rec.request_purchase_requisition()
            else:
                rec.state = 'cost_control'

    def set_ceo_approv(self):
    	for rec in self:
            if rec.price_total > 20000 :
                rec.check_price = True
                rec.state = 'done'
                rec.request_purchase_requisition()
            else:
                rec.state = 'ceo_approve'

    def set_cancel(self):
    	for rec in self:
            rec.state = 'cancel'

    def set_to_draft(self):
        for rec in self:
            rec.check_po = False
            rec.state = 'draft'

    
    @api.model
    def _prepare_pick_move(self, line=False, stock_id=False):
        pick_move = {
            'product_id' : line.product_id.id,
            'product_uom_qty' : line.qty_pick,
            'product_uom' : line.uom.id,
            'location_id' : self.delivery_type_id.default_location_src_id.id,
            'location_dest_id' : self.partner_id.property_stock_customer.id,
            'name' : line.product_id.name,
            'picking_type_id' : self.delivery_type_id.id,
            'picking_id' : stock_id.id,
            'custom_requisition_line_id' : line.id,
            'company_id' : line.requisition_id.company_id.id,
            'state': 'assigned',
        }
        return pick_move
    

    @api.model
    def _prepare_pick_vals(self, rec=False):
        picking_vals = {
            'partner_id' : rec.employee_id.sudo().address_home_id.id,
            #'min_date' : fields.Date.today(),
            'location_id' : rec.delivery_type_id.default_location_src_id.id,
            'location_dest_id' : rec.partner_id.property_stock_customer.id,
            'picking_type_id' : rec.delivery_type_id.id,
            'note' : rec.reason,
            'custom_requisition_id' : rec.id,
            'origin' : rec.name,
            'company_id' : rec.company_id.id, 

        }
        return picking_vals

############Purchase Order Values###################################
    @api.model
    def _prepare_purchase_requisition(self, rec=False):
        po_vals = {
            'vendor_id':rec.partner_id.id,
            'currency_id':rec.env.user.company_id.currency_id.id,
            'ordering_date':fields.Date.today(),
            # 'picking_type_id' : rec.recipt_type_id.id,
    #       company_id':rec.env.user.company_id.id,
            'company_id':rec.company_id.id,
            'custom_requisition_id':rec.id,
            'origin': rec.name,
            # 'in_project': True
        }
        return po_vals

    def _prepare_purchase_line(self, line=False, purchase_requisition=False):
        po_line_vals = {
                 'product_id': line.product_id.id,
                 # 'name':line.product_id.name,
                 'product_qty': line.qty,
                 'product_uom_id': line.uom.id,
                 # 'date_planned': fields.Date.today(),
                 'price_unit': line.price_unit,
                 'requisition_id': purchase_requisition.id,
                 'account_analytic_id': self.analytic_account_id.id,
                 # 'custom_requisition_line_id': line.id,
                 # 'in_project': True,
        }
        return po_line_vals


    def request_stock_picking(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']

        for rec in self:
            if not rec.requisition_line_ids:
                raise UserError(_('Please create some requisition lines.'))
            picking_vals = rec._prepare_pick_vals(rec)
            stock_id = stock_obj.sudo().create(picking_vals)

            # stock_id = stock_obj.sudo().create(picking_vals)
            po_dict = {}
            for line in rec.requisition_line_ids:
                if line.qty_pick !=0:
                   # if line.qty_pick and line.qty_po != 0 or line.qty_po == 0:
                    pick_move = rec._prepare_pick_move(line, stock_id)
                    move_id = move_obj.sudo().create(pick_move)

    def request_purchase_requisition(self):
        purchase_obj = self.env['purchase.requisition']
        purchase_line_obj = self.env['purchase.requisition.line']
        for rec in self:
            if not rec.requisition_line_ids:
                raise UserError(_('Please create some requisition lines.'))
            po_vals = rec._prepare_purchase_requisition(rec)   
            purchase_requisition = purchase_obj.sudo().create(po_vals)
            for line in rec.requisition_line_ids:
                if rec.partner_id: 
                    if line.qty_po !=0:
                        po_line_vals = rec._prepare_purchase_line(line, purchase_requisition)
                        purchase_line_obj.sudo().create(po_line_vals)

    def action_show_requisition(self):
        for rec in self:
            purchase_action = self.env.ref('purchase_requisition.action_purchase_requisition')
            purchase_action = purchase_action.read()[0]
            purchase_action['domain'] = str([('custom_requisition_id','=',rec.id)])
        return purchase_action



class MaterialPurchaseRequisitionLine(models.Model):
    _inherit = "material.purchase.requisition.line"

    qty = fields.Float(
        string='Quantity',
        default=0,
        required=True,
    )
    # uom_id = fields.Many2one(
    #     'uom.uom',#product.uom in odoo11
    #     string='Unit of Measure',
    #     readonly=True,
    # )
    qty_available = fields.Float(
        string='Availble',
        required=True,
        readonly=True
    )
    qty_pick = fields.Float(
        string='Done',
        required=True,
        readonly=True
    )
    qty_po = fields.Float(
        string='Remaining',
        required=True,
        readonly=True
    )
    price_unit = fields.Float(
        string='Price Unit',
        required=True,

    )
    check_po= fields.Boolean(
        string='Check Qty Remaining',
    )
    sub_total = fields.Float(
        compute='_compute_sup_amount',
        string='Subtotal',
    )
    uom = fields.Many2one(
        'uom.uom',#product.uom in odoo11
        string='Unit of Measure',
        required=True,
    )



    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            # line.description = line.product_id.name
            line.description = line.product_id.description_purchase
            line.uom = line.product_id.uom_po_id.id
            line.qty_available = line.product_id.qty_available
            line.price_unit = line.product_id.standard_price

    @api.onchange('qty')
    def onchange_quantity(self):
        for line in self:
            if line.qty <= line.qty_available and line.qty_available != 0:
                line.qty_pick = line.qty
                line.qty_po = 0
            elif line.qty_available == 0:
                line.qty_po = line.qty
                line.qty_pick = 0
            elif line.qty > line.qty_available:
                line.qty_pick = line.qty_available
                line.qty_po = line.qty - line.qty_available
            if line.qty_po != 0:
                line.check_po = True
            elif line.qty_po == 0:
                line.check_po = False


    @api.depends('qty_po', 'qty_pick', 'price_unit')
    def _compute_sup_amount(self):
        for line in self:
            if line.qty_po > 0:
                line.sub_total = line.price_unit*line.qty_po
            elif line.qty_po == 0:
                line.sub_total = line.price_unit*line.qty_pick

class service_type(models.Model):
    _name = 'service.type'
    _description = 'Service Type'

    name = fields.Char(
        string='',
        size=64,
        required=False,
        readonly=False,
    )

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'
    
    custom_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Requisitions',
        copy=False
    )
    


