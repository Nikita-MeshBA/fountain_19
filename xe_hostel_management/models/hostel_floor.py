""" Hostel Floor python file """
# pylint: disable= E0401, R0903
from odoo import models, fields


class HostelFloor(models.Model):
    """Hostel Floor class"""

    _name = "xe.hostel.floor"
    _description = "Hostel Floor"
    _rec_name = "floor_no"

    floor_no = fields.Char()
    hostel_id = fields.Many2one("xe.hostel")
    responsible_staff_id = fields.Many2one("hr.employee")
