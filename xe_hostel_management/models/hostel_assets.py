""" Hostel Assets python file """
# pylint: disable= E0401, R0903
from odoo import models, fields


class HostelAssets(models.Model):
    """Hostel Assets class"""
    _name = "xe.hostel.assets"
    _description = "Hostel Assets"
    _rec_name = "name"

    name = fields.Char()
    product_id = fields.Many2one('product.product')
    product_categ_id = fields.Many2one('product.category', related="product_id.categ_id")
    product_uom_id = fields.Many2one('uom.uom', related="product_id.uom_id")
    product_type = fields.Selection(
        [("consu", "Consumable"), ("service", "Service"), ('event_booth', 'Event Booth')], related="product_id.type"
    )
    product_image = fields.Binary(related="product_id.image_1920")
    hostel_id = fields.Many2one("xe.hostel")
    room_id = fields.Many2one("xe.hostel.room")
