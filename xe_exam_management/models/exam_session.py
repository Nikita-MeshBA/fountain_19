# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime

import xlsxwriter
from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class XeExamSession(models.Model):
    _name = "xe.exam.session"
    _inherit = ["mail.thread"]
    _description = "Exam Session"

    def _get_auto_session_name(self):
        is_auto_session_name = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_exam_management.is_auto_session_name")
        )
        return is_auto_session_name

    _sql_constraints = [
        (
            "exam_code_unique",
            "unique (exam_code)",
            "Code should be unique per exam session!",
        )
    ]

    name = fields.Char("Exam Session", size=256, required=True, tracking=True)
    course_id = fields.Many2one("xe.course", "Class", required=True, tracking=True)
    exam_code = fields.Char(
        "Exam Session Code",
        required=True,
        tracking=True,
        copy=False,
        default="Exam Code",
    )
    start_date = fields.Date(required=True, tracking=True)
    end_date = fields.Date(required=True, tracking=True)
    exam_ids = fields.One2many("xe.exam", "session_id", "Exam(s)")
    # old field
    exam_type = fields.Many2one("xe.exam.type", tracking=True)
    # new field
    exam_type_id = fields.Many2one("xe.exam.type", required=True, tracking=True)
    evaluation_type = fields.Selection(
        [("normal", "Normal"), ("grade", "Grade")],
        default="normal",
        required=True,
        tracking=True,
    )
    venue = fields.Char(tracking=True, default=lambda self: self.env.company.name)
    classroom_ids = fields.Many2many("xe.classroom")
    staff_id = fields.Many2one("hr.employee", "Exam Invigilator")
    staff_user_id = fields.Many2one("res.users", "Exam Invigilator User")
    is_exam_created = fields.Boolean("Exam Created")
    academic_term_id = fields.Many2one("xe.academic.terms")
    academic_year_id = fields.Many2one("xe.academic.year")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    is_auto_session = fields.Boolean(default=_get_auto_session_name)
    rubrics_ids = fields.One2many(
        "xe.rubrics.configuration", "exam_session_id", string="Rubrics Configuration"
    )
    subject_ids = fields.Many2many("xe.subject", compute="_compute_subject")
    state = fields.Selection([("draft", "Draft"), ("exams_created", "Exams Created"), ("done", "Done")], default="draft")
    course_evaluation_type = fields.Selection([
            ("1-3 CBC", "CBC"),
            ("8-4-4", "8-4-4"),
            ("Kindergarten", "Kindergarten"),
            ("Playgroup", "Playgroup"),
            ("Pre Primary", "Pre Primary"),
            ("Cambridge", "Cambridge"),
        ],
        related="course_id.evaluation_type"
    )

    @api.onchange("venue")
    def _onchange_venue(self):
        for i in self:
            if not i.venue:
                i.venue = i.company_id.name

    @api.constrains("start_date", "end_date")
    def _check_date_time(self):
        if self.start_date > self.end_date:
            raise ValidationError(_("End Date cannot be set before Start Date."))

    @api.onchange("course_id")
    def onchange_course(self):
        if self.course_id:
            class_room_rec = (
                self.env["xe.classroom"]
                .sudo()
                .search([("course_id", "in", self.course_id.ids)])
            )
            self.write({"classroom_ids": [(6, 0, class_room_rec.ids)]})
        else:
            self.write({"classroom_ids": [(6, 0, [])]})

    @api.onchange("course_id", "exam_type_id", "academic_term_id", "academic_year_id")
    def _set_name(self):
        is_auto_session = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_exam_management.is_auto_session_name")
        )
        if is_auto_session:
            name = ""
            code = ""
            if self.course_id:
                if self.course_id.name:
                    name += self.course_id.name + " "
                if self.course_id.code:
                    code += self.course_id.code
            if self.exam_type_id:
                if self.exam_type_id.name:
                    name += self.exam_type_id.name + " "
                if self.exam_type_id.code:
                    code += self.exam_type_id.code
            if self.academic_term_id:
                if self.academic_term_id.name:
                    name += self.academic_term_id.name + " "
                if self.academic_term_id.code:
                    code += self.academic_term_id.code
            if self.academic_year_id:
                if self.academic_year_id.name:
                    name += self.academic_year_id.name + " "
                if self.academic_year_id.code:
                    code += self.academic_year_id.code

            self.name = name.rstrip()
            self.exam_code = code.rstrip()

    def create_result_template(self):
        for exam in self.exam_ids:
            if exam.state != "done":
                raise ValidationError(
                    _(
                        "For results to be generated, all exams must be in the done stage."
                    )
                )
        result_template_count = self.env["xe.result.template"].search_count(
            [("exam_session_id", "=", self.id)]
        )
        if result_template_count > 0:
            return {
                "name": _("Results"),
                "type": "ir.actions.act_window",
                "view_mode": "tree,form",
                "res_model": "xe.result.template",
                "target": "current",
                "domain": [("exam_session_id", "=", self.id)],
            }
        else:
            ctx = {}
            ctx.update(
                {
                    "default_exam_session_id": self.id,
                    "default_name": self.name.rstrip() + " Result",
                }
            )
            return {
                "name": _("Results"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "xe.result.template",
                "target": "current",
                "context": ctx,
            }

    def create_exams_new(self):
        course_id = self.course_id
        exam_lines = []
        for i in self.classroom_ids:
            for subject in course_id.course_subject_line_ids:
                if subject.is_examinable:
                    start_date = datetime.combine(self.start_date, datetime.min.time())
                    end_date = datetime.combine(self.end_date, datetime.min.time())
                    exam_vals = {
                        "name": self.name + "/" + subject.name,
                        "exam_code": self.exam_code + "/" + subject.code + "/" + i.code,
                        "classroom_ids": [(6, 0, [i.id])],
                        "subject_id": subject.id,
                        "start_time": start_date,
                        "end_time": end_date,
                        "total_marks": 1,
                        "min_marks": 1,
                    }
                    if self.staff_id:
                        exam_vals["staff_id"] = self.staff_id.id
                    exam_lines.append([0, 0, exam_vals])
                else:
                    exam_vals = {}
        self.write({"exam_ids": exam_lines, "is_exam_created": True, "state": "exams_created"})

    def create_exams(self):
        if self.env.user.has_group(
            "xe_exam_management.group_subject_rubrics_configuration"
        ):
            ctx = {}
            ctx.update({"default_exam_session_id": self.id})
            return {
                "name": _("Confirm"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "exam.confirm.wizard",
                "target": "new",
                "context": ctx,
            }
        else:
            self.create_exams_new()

    def export_rubrics_file(self):
        rubrics_line_ids = self.env["xe.rubrics.configuration"].search_read(
            [("exam_session_id", "=", self.id)]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Rubrics")
        header_format = workbook.add_format({"bold": True})

        worksheet.set_column("A:A", 25)
        worksheet.set_column("B:B", 15)
        worksheet.set_column("C:C", 25)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 15)
        worksheet.write("A1", "Subject", header_format)
        worksheet.write("B1", "Code", header_format)
        worksheet.write("C1", "Description", header_format)
        worksheet.write("D1", "Minimum Marks", header_format)
        worksheet.write("E1", "Maximum Marks", header_format)

        if rubrics_line_ids:
            row = 1
            col = 0
            for line in rubrics_line_ids:
                worksheet.write(row, col, line["subject_id"][1])
                worksheet.write(row, col + 1, line["new_code_id"][1])
                worksheet.write(row, col + 2, line["name"])
                worksheet.write(row, col + 3, line["min_per"])
                worksheet.write(row, col + 4, line["max_per"])
                row += 1

        workbook.close()
        output.seek(0)
        generated_file = base64.encodebytes(output.read())
        output.close()
        attachment_data = {
            "name": "Session Rubrics.xls",
            "datas": generated_file,
        }
        att_id = self.env["ir.attachment"].create(attachment_data)
        return {
            "type": "ir.actions.act_url",
            "url": "web/content/%s?download=true" % att_id.id,
            "target": "self",
        }

    def import_rubrics_file(self):
        return {
            "name": _("Import Session Rubrics"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "import.session.rubrics",
            "target": "new",
        }

    @api.depends("exam_ids")
    def _compute_subject(self):
        for rec in self:
            if rec.exam_ids:
                rec.subject_ids = [(6, 0, rec.exam_ids.mapped("subject_id").ids)]
            else:
                rec.subject_ids = [(6, 0, [])]

    def add_exams(self):
        new_subject_ids = []
        subject_ids = self.env["xe.subject"].search([('course_ids', 'in', [self.course_id.id])])
        exam_subject_ids = self.exam_ids.mapped("subject_id.id")
        for subject in subject_ids:
            if subject.id not in exam_subject_ids:
                new_subject_ids.append(subject.id)
        return {
            "name": _("Add Exams"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "add.exam.wizard",
            "target": "new",
            "context": {
                "default_session_id": self.id,
                "default_class_id": self.course_id.id,
                "default_classroom_ids": [(6, 0, self.classroom_ids.ids)],
                "default_start_date": self.start_date,
                "default_end_date": self.end_date,
                "default_new_subject_ids": [(6, 0, new_subject_ids)],
            }
        }
