from odoo import models, fields, _


class Student(models.Model):
    _inherit = "xe.student"

    head_teacher_name = fields.Char(
        related="course_id.head_teacher_id.name", string="Head Teacher Name"
    )
    head_teacher_mobile = fields.Char(
        related="course_id.head_teacher_id.mobile_phone", string="Head Teacher Mobile"
    )
    head_teacher_phone = fields.Char(
        related="course_id.head_teacher_id.work_phone", string="Head Teacher Phone"
    )
    head_teacher_email = fields.Char(
        related="course_id.head_teacher_id.work_email", string="Head Teacher Email"
    )
    class_teacher_name = fields.Char(
        related="classroom_id.teacher_id.name", string="Class Teacher Name"
    )
    class_teacher_mobile = fields.Char(
        related="classroom_id.teacher_id.mobile_phone", string="Class Teacher Mobile"
    )
    class_teacher_phone = fields.Char(
        related="classroom_id.teacher_id.work_phone", string="Class Teacher Phone"
    )
    class_teacher_email = fields.Char(
        related="classroom_id.teacher_id.work_email", string="Class Teacher Email"
    )
    markregister_line_ids = fields.One2many(
        "xe.marksheet.line",
        "student_id",
        domain=[("register_state", "=", "validated")],
        string="Marksheet Line",
        readonly=True,
    )

    def action_view_exam_lines(self):
        marksheet_lines = self.env["xe.marksheet.line"].search(
            [("student_id", "=", self.id)]
        )
        return {
            "name": _("Marksheet Lines"),
            "view_mode": "tree",
            "res_model": "xe.marksheet.line",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", marksheet_lines.ids)],
        }
