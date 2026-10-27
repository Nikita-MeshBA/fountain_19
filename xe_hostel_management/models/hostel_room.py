""" Hostel Room python file """
# pylint: disable= E0401, R0903
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HostelRoom(models.Model):
    """Hostel Room class"""

    _name = "xe.hostel.room"
    _description = "Hostel Room"
    _rec_name = "name"

    name = fields.Char()
    code = fields.Char()
    capacity = fields.Integer()
    hostel_id = fields.Many2one("xe.hostel")
    floor_id = fields.Many2one("xe.hostel.floor")
    allocated_students = fields.Char()
    vacancy = fields.Char()
    bed_ids = fields.One2many("xe.hostel.bed", "room_id")
    asset_ids = fields.One2many("xe.hostel.assets", "room_id")


class HostelRoomMember(models.Model):
    """Hostel Room Member class"""

    _name = "xe.hostel.room.member"

    hostel_id = fields.Many2one("xe.hostel")
    room_id = fields.Many2one("xe.hostel.room")
    bed_id = fields.Many2one("xe.hostel.bed")
    allocated_date = fields.Date()
    vacated_date = fields.Date()
    hostel_admission_id = fields.Many2one("xe.hostel.admission")

    @api.onchange("bed_id")
    def _onchnage_bed_id(self):
        for rec in self:
            if rec.bed_id:
                hostel_admission_id = self.env["xe.hostel.admission"].search(
                    [("bed_id", "=", rec.bed_id.id), ("state", "=", "allocated")],
                    order="id desc",
                    limit=1,
                )
                if (
                    hostel_admission_id
                    and hostel_admission_id.name
                    and hostel_admission_id.number
                ):
                    raise ValidationError(
                        _(
                            "Bed - %s has already been allocated to %s - %s."
                            % (hostel_admission_id.bed_id.product_id.name, hostel_admission_id.number, hostel_admission_id.name)
                        )
                    )
                if (
                    hostel_admission_id
                    and hostel_admission_id.name
                    and not hostel_admission_id.number
                ):
                    raise ValidationError(
                        _(
                            "Bed - %s has already been allocated to %s."
                            % (hostel_admission_id.bed_id.product_id.name, hostel_admission_id.name)
                        )
                    )
                if (
                    hostel_admission_id
                    and not hostel_admission_id.name
                    and hostel_admission_id.number
                ):
                    raise ValidationError(
                        _(
                            "Bed - %s has already been allocated to %s."
                            % (hostel_admission_id.bed_id.product_id.name, hostel_admission_id.number)
                        )
                    )
