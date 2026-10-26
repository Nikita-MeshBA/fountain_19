# pylint: disable=E0401,C0114,C0115
from odoo import models, fields, api


class DayWiseSessions(models.Model):
    _name = "week.day.sessions"
    _description = "Week Day Sessions"

    week_day = fields.Selection(
        [
            ("mon", "Monday"),
            ("tues", "TuesDay"),
            ("wed", "Wednesday"),
            ("thurs", "Thurs"),
            ("fri", "Friday"),
            ("sat", "Saturday"),
            ("sun", "Sunday"),
        ]
    )
    timing_id = fields.Many2one("xe.timings", "Timing")
    start_time = fields.Float("Start Time", related="timing_id.start_time")
    end_time = fields.Float("End Time", related="timing_id.end_time")
    duration = fields.Float("Duration", related="timing_id.duration")
    subject_id = fields.Many2one("xe.subject", "Subject")
    teacher_id = fields.Many2one(
        "hr.employee", "Teacher", domain=[("teach_type", "=", "teaching")]
    )
    timetable_id = fields.Many2one("xe.timetable.sessions", "Timetable Sessions")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    course_id = fields.Many2one("xe.course", "Class", related="timetable_id.course_id")
    academic_term_id = fields.Many2one(
        "xe.academic.terms", "Term", related="timetable_id.academic_term_id"
    )
    class_room_id = fields.Many2one("xe.classroom", string="Classroom")

    @api.onchange("course_id", "subject_id", "timing_id")
    def _subject_domain(self):
        domain = {}
        for line in self:
            if line.course_id.id:
                subjects = line.course_id.course_subject_line_ids.ids
                domain["subject_id"] = [("id", "in", subjects)]
        return {"domain": domain}
