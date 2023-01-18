
from odoo import models, fields, api, _
from datetime import timedelta, datetime, date

class Location(models.Model):
    _inherit = 'stock.location'

    main_location = fields.Boolean(
        string='Main Location'
    )