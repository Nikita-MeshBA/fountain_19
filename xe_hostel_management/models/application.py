""" Application python file """
# pylint: disable= E0401, R0903, C0116
from odoo import models, fields


class XeApplication(models.Model):
    """Application inherit class"""

    _inherit = "xe.application"

    is_hostel_facility = fields.Boolean()

    def action_enroll(self):
        result = super(XeApplication, self).action_enroll()
        student_id = self.env["xe.student"].search(
            [("roll_number", "=", self.admission_number)], limit=1, order="id desc"
        )
        if self.is_hostel_facility and student_id:
            vals = {
                "member_type": "is_student",
                "student_id": student_id.id,
                "state": "draft",
                "gender": student_id.gender or False,
                "dob": student_id.dob or False,
                "phone": "",
                "mobile": "",
                "email": student_id.email or "",
                "street": student_id.street or "",
                "street2": student_id.street2 or "",
                "zip": student_id.zip or "",
                "city": student_id.city or "",
                "state_id": student_id.state_id and student_id.state_id.id or False,
                "country_id": student_id.country_id
                and student_id.country_id.id
                or False,
            }
            admission_id = (
                self.env["xe.hostel.admission"]
                .with_context({"show_roll_number": True})
                .create(vals)
            )
            student_id.is_hostel_facility = True
        return result
