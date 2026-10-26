# pylint: disable=E0401,C0114,C0115,C0116
from odoo import models, fields, _


class XeSessionDetailedLines(models.Model):
    _name = "xe.session.lines"
    _inherit = ["mail.thread"]
    _description = "Time Table Sessions"

    def _compute_get_users(self):
        students = self.env["xe.student.course"].search(
            [("course_id", "=", self.course_id.id), ("term_id", "=", self.term_id.id)]
        )
        users = []
        if students:
            for stud in students:
                users.append(stud.mapped("student_id").mapped("user_id").id)
        self.student_users_ids = [(6, 0, users)]

    name = fields.Char()
    session_date = fields.Date()
    day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ]
    )
    timing_id = fields.Many2one("xe.timings", "Timing")
    start_time = fields.Float("Start Time", related="timing_id.start_time")
    end_time = fields.Float("End Time", related="timing_id.end_time")
    duration = fields.Float("Duration", related="timing_id.duration")
    subject_id = fields.Many2one("xe.subject", "Subject")
    teacher_id = fields.Many2one("hr.employee", "Teacher")
    timetable_id = fields.Many2one(
        "xe.timetable.sessions", "Timetable Sessions", ondelete="cascade"
    )
    term_id = fields.Many2one("xe.term", "Term")
    course_id = fields.Many2one("xe.course", "Class")
    student_users_ids = fields.Many2many(
        "res.users",
        "dummy_stud_usrs",
        "sess_id",
        "usr_id",
        string="Student Users",
        compute="_compute_get_users",
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    academic_term_id = fields.Many2one("xe.academic.terms", string="Term")
    class_room_id = fields.Many2one("xe.classroom", string="Classroom")

    def generate_timetable(self):
        action = {
            "name": _("Generate Timetable Sessions"),
            "type": "ir.actions.act_window",
            "res_model": "xe.timetable.sessions",
            "target": "current",
            "view_mode": "form",
        }
        return action

    def name_get(self):
        result = []
        for obj in self:
            name = obj.name + "(" + str(obj.session_date) + ")"
            result.append((obj.id, name))
        return result
