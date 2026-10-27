""" Hostel python file """
# pylint: disable= E0401, R0903, C0116
from odoo import models, fields


class Hostel(models.Model):
    """Hostel class"""

    _name = "xe.hostel"
    _description = "Hostel"
    _rec_name = "name"

    name = fields.Char()
    code = fields.Char()
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state", domain="[('country_id', '=?', country_id)]"
    )
    country_id = fields.Many2one("res.country")
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    warden_id = fields.Many2one("hr.employee")
    capacity = fields.Integer(compute="_compute_vacancy_count")
    total_floors = fields.Char()
    vacancy = fields.Integer(compute="_compute_vacancy_count")
    total_rooms = fields.Integer(compute="_compute_room_count")
    student_ids = fields.Many2many("xe.student", compute="_compute_student_count")
    room_ids = fields.One2many("xe.hostel.room", "hostel_id")
    admission_count = fields.Integer(compute="_compute_student_count")
    asset_ids = fields.One2many("xe.hostel.assets", "hostel_id")

    def get_hostel_admission(self):
        admission_ids = self.env["xe.hostel.admission"].search(
            [("hostel_id", "=", self.id)]
        )
        tree_view_id = self.env.ref(
            "xe_hostel_management.xe_hostel_admission_tree_view"
        ).id
        form_view_id = self.env.ref(
            "xe_hostel_management.xe_hostel_admission_form_view"
        ).id
        return {
            "name": "Hostel Admission",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "view_ids": [(tree_view_id, "tree"), (form_view_id, "form")],
            "res_model": "xe.hostel.admission",
            "target": "current",
            "domain": [
                ("id", "in", admission_ids.ids),
            ],
        }

    def _compute_student_count(self):
        for rec in self:
            admission_ids = self.env["xe.hostel.admission"].search(
                [
                    ("hostel_id", "=", rec.id),
                    ("state", "=", "allocated"),
                    ("member_type", "=", "is_student"),
                ]
            )
            if admission_ids:
                rec.student_ids = [(6, 0, admission_ids.mapped("student_id").ids)]
                rec.admission_count = len(admission_ids)
            else:
                rec.student_ids = False
                rec.admission_count = 0

    def _compute_vacancy_count(self):
        for rec in self:
            admission_ids = self.env["xe.hostel.admission"].search(
                [
                    ("hostel_id", "=", rec.id),
                    ("state", "=", "allocated"),
                    ("member_type", "=", "is_student"),
                ]
            )
            hostel_capacity = sum(
                self.env["xe.hostel.room"]
                .search([("hostel_id", "=", rec.id)])
                .mapped("capacity")
            )

            if hostel_capacity:
                rec.capacity = hostel_capacity
                rec.vacancy = hostel_capacity - len(admission_ids)
            else:
                rec.capacity = 0
                rec.vacancy = 0

    def _compute_room_count(self):
        for rec in self:
            room_ids = self.env["xe.hostel.room"].search([("hostel_id", "=", rec.id)])
            if room_ids:
                rec.total_rooms = len(room_ids)
            else:
                rec.total_rooms = 0
