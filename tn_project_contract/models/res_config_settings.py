# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_works_id = fields.Many2one('product.product', 'Product Works', config_parameter='tn_project_contract.product_works_id')
    product_adv_pay_id = fields.Many2one('product.product', 'Product advance payment', config_parameter='tn_project_contract.product_adv_pay_id')
    product_retain_warranty_id = fields.Many2one('product.product', 'Product retained warenty', config_parameter='tn_project_contract.product_retain_warranty_id')
