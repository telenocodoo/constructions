# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    is_pay = fields.Boolean('Is Payment')
    check_invoice = fields.Boolean('Invoiced')
    amount_works = fields.Float('Amount  Works')
    project_contract_id = fields.Many2one('project.contract', 'Project Contract')

    @api.depends('ac_purchase_id', 'adv_payment', 'amount_total')
    def compute_all_payment(self):
        for move in self:
            if move.move_type == 'in_invoice' and move.is_payment == True:
                move.adv_payment = move.advance_pay
                move.net_invoice = move.amount_total

            if move.move_type == 'out_invoice' and move.is_pay == True:
                move.adv_payment = move.advance_pay
                move.net_invoice = move.amount_total

        # ========= Create invoice from Purchase  Order ================================
            if move.move_type == 'in_invoice' and move.is_payment == False:
                if move.invoice_line_ids:
                    move.adv_payment = [-line.price_unit for line in self.invoice_line_ids][1]
                    move.retention = (move.advance_pay*move.ac_purchase_id.retained_warranty)/100
                    move.net_invoice = move.amount_total

        # ========= Create invoice from Project Contract ================================
            if move.move_type == 'out_invoice' and move.is_pay == False:
                if move.invoice_line_ids:
                    move.adv_payment = [-line.price_unit for line in move.invoice_line_ids][1]
                    move.retention = (move.amount_works*move.project_contract_id.retained_warranty)/100
                    move.net_invoice = move.amount_total  

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    project_contract_line_id = fields.Many2one('project.contract', 'Project Contract')