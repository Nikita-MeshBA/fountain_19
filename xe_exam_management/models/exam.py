# -*- coding: utf-8 -*-
import datetime

from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _


class XeExam(models.Model):
    _name = "xe.exam"
    _inherit = "mail.thread"
    _description = "Exam"

    _sql_constraints = [
        ("unique_exam_code", "unique(exam_code)", "Code should be unique per exam!")
    ]

    session_id = fields.Many2one("xe.exam.session", "Exam Session")
    course_id = fields.Many2one(
        "xe.course", related="session_id.course_id", store=True, readonly=True
    )
    subject_id = fields.Many2one(
        "xe.subject", required=True, domain=[("is_parent", "=", False)]
    )
    # sequence = fields.Integer(related="subject_id.sequence", store=True)
    exam_code = fields.Char(required=True)
    attendees_line_ids = fields.One2many("xe.exam.attendees", "exam_id", "Attendees")
    start_time = fields.Datetime(required=True)
    end_time = fields.Datetime(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("schedule", "Scheduled"),
            ("held", "Held"),
            ("result_updated", "Result Updated"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        readonly=True,
        default="draft",
        tracking=True,
    )
    note = fields.Text()
    name = fields.Char("Exam", size=256, required=True)
    total_marks = fields.Integer(required=True)
    min_marks = fields.Integer("Passing Marks", required=True)
    classroom_ids = fields.Many2many(
        "xe.classroom",
        "classroom_exam_rel",
        "exam_id",
        "classroom_id",
    )
    staff_id = fields.Many2one(
        "hr.employee",
        "Class Exam Invigilator",
        domain="[('teach_type','=','teaching')]",
    )
    staff_user_id = fields.Many2one("res.users", "Exam Invigilator User")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    # course_eval_type_bool = fields.Boolean(
    #     compute="_compute_course_eval_type_bool", store=True
    # )

    # @api.depends("session_id")
    # def _compute_course_eval_type_bool(self):
    #     for rec in self:
    #         if (
    #             rec.session_id.course_id.evaluation_type
    #             and rec.session_id.course_id.evaluation_type == "1-3 CBC"
    #         ):
    #             rec.course_eval_type_bool = True
    #         else:
    #             rec.course_eval_type_bool = False

    def findout_student_attendees(self, exams):
        student_ids = []
        for exam in exams:
            exam = self.browse(exam)

            attendees_line_ids = exam.attendees_line_ids
            for line in attendees_line_ids:
                student_ids.append(line.student_id and line.student_id.id)
        student_ids = list(set(student_ids))
        return student_ids

    def act_done(self):
        subject_obj = self.subject_id
        session_id = self.session_id and self.session_id.id
        evaluation_type = (
            self.session_id
            and self.session_id.course_id
            and self.session_id.course_id.evaluation_type
        )
        start_time = self.start_time
        end_time = self.end_time
        total_marks = 100
        exam = self.session_id.name

        if subject_obj.parent_id and subject_obj.parent_id.name:
            exam = subject_obj.parent_id.code + str(self.start_time)
        exam_code = exam

        parent_subject_id = (
            subject_obj and subject_obj.parent_id and subject_obj.parent_id.id or False
        )
        subjects = (
            self.env["xe.subject"]
            .search(
                [("parent_id", "=", parent_subject_id), ("id", "!=", subject_obj.id)]
            )
            .mapped("id")
        )
        len_subjects = len(subjects)
        exams = self.search(
            [
                ("subject_id", "in", subjects),
                ("state", "=", "done"),
                ("session_id", "=", session_id),
                ("classroom_ids", "in", self.classroom_ids.ids),
            ]
        ).mapped("id")
        len_exams = len(exams)

        # need to perform this action,after all sub exams
        if (
            len_exams == len_subjects
            and evaluation_type in ("1-3 CBC", "8-4-4")
            and parent_subject_id
        ):
            sub_subjects = (
                self.env["xe.subject"]
                .search([("parent_id", "=", parent_subject_id)])
                .mapped("id")
            )
            exams = self.search(
                [
                    ("subject_id", "in", sub_subjects),
                    ("session_id", "=", session_id),
                    ("classroom_ids", "in", self.classroom_ids.ids),
                ]
            ).mapped("id")
            exam_attandee_students = self.findout_student_attendees(exams)
            parent_subject_total = 0
            parent_subject_min = 0
            attendees_vals = []
            for student in exam_attandee_students:
                attendees = self.env["xe.exam.attendees"].search(
                    [("exam_id", "in", exams), ("student_id", "=", student)]
                )
                obtained_marks = 0
                overall_marks = 0
                room_id = False
                status = "present"
                for line in attendees:
                    marks = line.marks
                    total_marks = line.exam_id.total_marks
                    parent_subject_total += total_marks
                    parent_subject_min += line.exam_id.min_marks
                    obtained_marks = obtained_marks + marks
                    if line.status == "absent":
                        status = "absent"

                    overall_marks = overall_marks + total_marks
                    room_id = line.room_id and line.room_id.id or False

                if total_marks <= 0:
                    raise UserError(
                        _("overall marks cannot be less than or equal to zero")
                    )

                new_marks = (obtained_marks / overall_marks) * 100
                new_marks = round(new_marks)

                new_attendees_vals = {
                    "student_id": student,
                    "room_id": room_id,
                    "marks": new_marks,
                    "status": status,
                }
                attendees_vals.append((0, 0, new_attendees_vals))

            parent_subject_min = round(
                ((parent_subject_min / parent_subject_total) * 100), 2
            )
            parent_subject_exam = self.search(
                [
                    ("subject_id", "in", [parent_subject_id]),
                    ("session_id", "=", session_id),
                    ("classroom_ids", "in", self.classroom_ids.ids),
                ]
            )
            new_exam_values = {
                "subject_id": parent_subject_id,
                "session_id": session_id,
                "start_time": start_time,
                "end_time": end_time,
                "total_marks": 100,
                "min_marks": parent_subject_min,
                "state": "result_updated",
                "attendees_line_ids": attendees_vals,
            }
            if parent_subject_exam:
                if parent_subject_exam.attendees_line_ids:
                    parent_subject_exam.sudo().write({"attendees_line_ids": False})
                parent_subject_exam.write(new_exam_values)
            else:
                new_exam_values["name"] = exam
                new_exam_values["exam_code"] = exam_code
                self.create(new_exam_values)
        self.state = "done"

    def get_contract_template(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {"exam_id": self.id},
        }
        return self.env.ref(
            "xe_exam_management.exam_attendee_report_xlsx"
        ).report_action(self, data=data)

    @api.constrains("total_marks", "min_marks")
    def _check_marks(self):
        for line in self:
            if line.total_marks <= 0.0 or line.min_marks <= 0.0:
                raise ValidationError(_("Enter proper marks!"))
            if line.min_marks > line.total_marks:
                raise ValidationError(
                    _("Passing Marks can't be greater than Total Marks")
                )

    @api.constrains("start_time", "end_time")
    def _check_date_time(self):
        for line in self:
            session_start = datetime.datetime.combine(
                fields.Date.from_string(line.session_id.start_date), datetime.time.min
            )
            session_end = datetime.datetime.combine(
                fields.Date.from_string(line.session_id.end_date), datetime.time.max
            )
            start_time = fields.Datetime.from_string(line.start_time)
            end_time = fields.Datetime.from_string(line.end_time)
            if start_time > end_time:
                raise ValidationError(_("End Time cannot be set before Start Time."))
            elif (
                start_time < session_start
                or start_time > session_end
                or end_time < session_start
                or end_time > session_end
            ):
                raise ValidationError(
                    _("Exam Time should in between Exam Session Dates.")
                )

    def act_result_updated(self):
        self.state = "result_updated"

    def act_done(self):
        self.state = "done"

    def act_draft(self):
        self.state = "draft"
        self.attendees_line_ids = False

    def act_cancel(self):
        self.state = "cancel"

    def action_held_exam(self):
        domain = []
        if self.session_id.course_id:
            domain.append(("course_id", "=", self.session_id.course_id.id))
        if self.session_id.classroom_ids:
            domain.append(("classroom_id", "in", self.classroom_ids.ids))
        students = self.env["xe.student"].search(domain)
        if self.subject_id.subject_mode == "yes":
            students = students.filtered(
                lambda l: self.subject_id in l.elective_subjects_ids
            )
        exam_attendees = []
        for student in students:
            attendee_vals = {
                "status": "present",
                "course_id": self.course_id.id,
                # "term_id": self.term_id.id,
                "student_id": student.id,
            }
            exam_attendees.append((0, 0, attendee_vals))
        self.attendees_line_ids = exam_attendees
        self.state = "held"

    def act_held(self):
        result_template = self.env["xe.result.template"].search(
            [("exam_session_id", "=", self.session_id.id)]
        )
        result_lines = self.env["xe.result.line"].search([("exam_id", "=", self.id)])
        if result_template and result_lines:
            raise ValidationError(
                _(
                    "Cannot reset back to Held as the marksheet lines are alerady created."
                )
            )
        self.state = "held"

    def action_create_held_exam(self):
        for exam in self:
            if exam.state == "draft":
                exam.action_held_exam()
