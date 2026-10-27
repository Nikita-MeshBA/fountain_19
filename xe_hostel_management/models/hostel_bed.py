""" Hostel Bed python file """
# pylint: disable= E0401, R0903
from odoo import models, fields


class HostelBed(models.Model):
    """Hostel Bed class"""
    _name = "xe.hostel.bed"
    _discription = "Hostel Bed"
    _rec_name = "name"

    name = fields.Char()
    product_id = fields.Many2one('product.product')
    product_categ_id = fields.Many2one('product.category', related="product_id.categ_id")
    product_uom_id = fields.Many2one('uom.uom', related="product_id.uom_id")
    product_image = fields.Image(related="product_id.image_1920")
    product_type = fields.Selection(
        [("consu", "Consumable"), ("service", "Service"), ('event_booth', 'Event Booth')], related="product_id.type"
    )
    room_id = fields.Many2one("xe.hostel.room")
    bed_category_id = fields.Many2one('xe.hostel.bed.category')
    floor_id = fields.Many2one('xe.hostel.floor', related="room_id.floor_id")
    student_id = fields.Many2one('xe.student')

class HostelBedCategory(models.Model):
    """Hostel Bed Category class"""
    _name = "xe.hostel.bed.category"
    _discription = "Hostel Bed Category"

    name = fields.Char()