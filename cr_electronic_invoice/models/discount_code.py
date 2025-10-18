from odoo import models, fields


class DiscountCode(models.Model):
    _name = "discount.code"
    _description = 'Discount Code'
    active = fields.Boolean(
        default=True
    )
    code = fields.Char()
    name = fields.Char()
