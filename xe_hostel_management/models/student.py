""" Student python file """
# pylint: disable= E0401, R0903, C0116
from odoo import models, fields, api


class XeStudent(models.Model):
    """Student inherit class"""

    _inherit = "xe.student"

    is_hostel_facility = fields.Boolean()
    hostel_id = fields.Many2one("xe.hostel", compute="_compute_hostel_details")
    room_id = fields.Many2one("xe.hostel.room", compute="_compute_hostel_details")
    bed_id = fields.Many2one("xe.hostel.bed", compute="_compute_hostel_details")

    def _compute_hostel_details(self):
        for rec in self:
            hostel_admission_id = self.env["xe.hostel.admission"].search(
                [("student_id", "=", rec.id), ("state", "=", "allocated")],
                limit=1,
                order="id DESC",
            )
            if hostel_admission_id:
                rec.hostel_id = (
                    hostel_admission_id.hostel_id
                    and hostel_admission_id.hostel_id.id
                    or False
                )
                rec.room_id = (
                    hostel_admission_id.room_id
                    and hostel_admission_id.room_id.id
                    or False
                )
                rec.bed_id = (
                    hostel_admission_id.bed_id
                    and hostel_admission_id.bed_id.id
                    or False
                )
            else:
                rec.hostel_id = False
                rec.room_id = False
                rec.bed_id = False

    def _compute_display_name(self):
        for record in self:
            if self.env.context.get("show_roll_number", False):
                record.display_name = record.roll_number
            else:
                record.display_name = record.name

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        recs = self.browse()
        if name:
            if self.env.context.get("show_roll_number", False):
                recs = self.search(
                    [("roll_number", operator, name)] + args, limit=limit
                )
            else:
                recs = self.search([("name", operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([("name", operator, name)] + args, limit=limit)

        records = []
        if recs:
            for rec in recs:
                records.append((rec.id, rec.display_name))
        return records
