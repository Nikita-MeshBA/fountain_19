# pylint: disable=E0401,C0114,C0115,C0116
import binascii
import tempfile
from datetime import timedelta

import xlrd
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, _


class XeTimetableSessions(models.Model):
    _name = "xe.timetable.sessions"
    _inherit = ["mail.thread"]
    _description = "Time Table"

    name = fields.Char(default="New")
    course_id = fields.Many2one("xe.course", "Class")
    term_id = fields.Many2one("xe.term", "Term")
    academic_term_id = fields.Many2one("xe.academic.terms", string="Term")
    from_date = fields.Date()
    to_date = fields.Date()
    state = fields.Selection(
        [("draft", "Draft"), ("configured", "Confirmed"), ("cancel", "Cancelled")],
        default="draft",
        tracking=True,
    )
    sun_sessions_ids = fields.One2many(
        "week.day.sessions",
        "timetable_id",
        domain=[("week_day", "=", "sun")],
        string="Sunday",
    )
    mon_sessions_ids = fields.One2many(
        "week.day.sessions",
        "timetable_id",
        domain=[("week_day", "=", "mon")],
        string="Monday",
    )
    tues_sessions_ids = fields.One2many(
        "week.day.sessions",
        "timetable_id",
        domain=[("week_day", "=", "tues")],
        string="Tuesday",
    )
    wed_sessions_ids = fields.One2many(
        "week.day.sessions",
        "timetable_id",
        domain=[("week_day", "=", "wed")],
        string="Wednesday",
    )
    thurs_sessions_ids = fields.One2many(
        "week.day.sessions",
        "timetable_id",
        domain=[("week_day", "=", "thurs")],
        string="Thursday",
    )
    fri_sessions_ids = fields.One2many(
        "week.day.sessions",
        "timetable_id",
        domain=[("week_day", "=", "fri")],
        string="Friday",
    )
    sat_sessions_ids = fields.One2many(
        "week.day.sessions",
        "timetable_id",
        domain=[("week_day", "=", "sat")],
        string="Saturday",
    )
    applicable_staff_ids = fields.Many2many(
        "hr.employee", "period_staff_rel", "session_id", "staff_id", string="Staffs"
    )
    file_name = fields.Char()
    upload_file = fields.Binary("File")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    is_upload = fields.Boolean("Uploaded the Session")

    def create_sessions(self, sess, day, day_name):
        session_line_obj = self.env["xe.session.lines"]
        values = {
            "timetable_id": self.id,
            "name": sess.timing_id.name,
            "timing_id": sess.timing_id.id,
            "teacher_id": sess.teacher_id.id,
            "subject_id": sess.subject_id.id,
            "course_id": self.course_id.id,
            "session_date": day,
            "day": str(day_name),
            "academic_term_id": sess.academic_term_id.id,
            "class_room_id": sess.class_room_id.id,
        }
        partners = []
        students = self.env["xe.student"].search(
            [("course_id", "=", self.course_id.id)]
        )
        if students:
            for stud in students:
                partners.append(stud.mapped("partner_id").id)
        partners.append(sess.teacher_id.mapped("partner_id").id)
        obj = session_line_obj.create(values)
        obj.message_subscribe(partner_ids=partners)

    def configure_session(self):
        others = self.env["xe.timetable.sessions"].search(
            [
                ("course_id", "=", self.course_id.id),
                ("from_date", ">=", self.from_date),
                ("to_date", "<=", self.to_date),
                ("state", "=", "configured"),
            ]
        )
        if others.ids:
            raise UserError(
                _("There is already a configured record with the given data")
            )
        self.name = (
            "Timetable of "
            + self.course_id.name
            + " ("
            + self.from_date.strftime("%d-%m-%Y")
            + " to "
            + self.to_date.strftime("%d-%m-%Y")
            + ")"
        )
        delta = self.to_date - self.from_date
        for i in range(delta.days + 1):
            day = self.from_date + timedelta(days=i)
            week_day = day.weekday()

            if week_day == 0:
                for sess in self.mon_sessions_ids:
                    self.create_sessions(sess, day, week_day)
            if week_day == 1:
                for sess in self.tues_sessions_ids:
                    self.create_sessions(sess, day, week_day)
            if week_day == 2:
                for sess in self.wed_sessions_ids:
                    self.create_sessions(sess, day, week_day)
            if week_day == 3:
                for sess in self.thurs_sessions_ids:
                    self.create_sessions(sess, day, week_day)
            if week_day == 4:
                for sess in self.fri_sessions_ids:
                    self.create_sessions(sess, day, week_day)
            if week_day == 5:
                for sess in self.sat_sessions_ids:
                    self.create_sessions(sess, day, week_day)
            if week_day == 6:
                for sess in self.sun_sessions_ids:
                    self.create_sessions(sess, day, week_day)
        self.state = "configured"

    def cancel_session(self):
        session_line_obj = self.env["xe.session.lines"]
        sessions = session_line_obj.search([("timetable_id", "=", self.id)])
        if sessions:
            for obj in sessions:
                obj.unlink()
        self.state = "cancel"

    def reset_to_draft(self):
        self.state = "draft"

    def upload_sessions(self):
        file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        file.write(binascii.a2b_base64(self.upload_file))
        file.seek(0)
        workbook = xlrd.open_workbook(file.name)
        sheet = workbook.sheet_by_index(0)
        for session in self:
            if not self.upload_file:
                raise ValidationError(_("Please Upload the File"))
            for row_no in range(sheet.nrows):
                if row_no > 0:
                    line = list(
                        map(
                            lambda row: isinstance(row.value, str)
                            and row.value.encode("utf-8")
                            or str(row.value),
                            sheet.row(row_no),
                        )
                    )
                    if line[0]:
                        line[0] = line[0].decode("utf-8")
                    if line[1]:
                        line[1] = line[1].decode("utf-8")
                    if line[2]:
                        line[2] = line[2].decode("utf-8")
                    if line[3]:
                        line[3] = line[3].decode("utf-8")
                    if line[4]:
                        line[4] = line[4].decode("utf-8")

                    line_day = str(line[3].lower().replace(" ", ""))
                    week_day = line_day.lower().replace("day", "")
                    if week_day == "wednes":
                        week_day = "wed"
                    timing_name = line[1]
                    timing_id = self.env["xe.timings"].search(
                        [("name", "=", timing_name)]
                    )
                    if timing_id and len(timing_id) > 1:
                        raise UserError(
                            _("There are multiple timing records for " + timing_name)
                        )
                    if timing_id:
                        teacher = False
                        if line[0]:
                            teacher = self.env["hr.employee"].search(
                                [("name", "=", line[0])]
                            )
                        subject = False
                        if line[2]:
                            subject = self.env["xe.subject"].search(
                                [("name", "=", line[2])]
                            )
                        classroom = line[4]
                        if classroom:
                            classroom = self.env["xe.classroom"].search(
                                [("name", "=", classroom)]
                            )
                        week_day_session_vals = {
                            "timetable_id": self.id,
                            "subject_id": subject.id or False,
                            "timing_id": timing_id.id,
                            "teacher_id": teacher.id or False,
                            "week_day": week_day,
                            "class_room_id": classroom.id or False,
                        }
                        self.env["week.day.sessions"].create(week_day_session_vals)
                        self.is_upload = True
                    else:
                        raise UserError(_("There is no timing " + str(timing_name)))
