# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116
import datetime
import logging
from datetime import datetime, date

from odoo.exceptions import UserError

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AttendanceManagement(models.Model):
    _name = "xe.student.attendance"
    _inherit = ["mail.thread"]
    _description = "Attendance Sheet"

    @api.onchange("teacher_user_id")
    def _get_teacher(self):
        for line in self:
            if line.teacher_user_id.id:
                teacher = self.env["hr.employee"].search(
                    [("user_id", "=", line.teacher_user_id.id)]
                )
                if teacher.id:
                    line.teacher_id = teacher.id
                else:
                    line.teacher_id = False

    name = fields.Char(default="New")
    course_id = fields.Many2one("xe.course", string="Class")
    term_id = fields.Many2one("xe.term", "Term")
    attendance_date = fields.Date(
        "Date", default=lambda self: date.today(), tracking=True
    )
    teacher_user_id = fields.Many2one("res.users", string="Teacher")
    teacher_id = fields.Many2one("hr.employee", string="Teacher")
    session_line_id = fields.Many2one("xe.session.lines", "Session")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Confirmed"),
            ("approved", "Approved"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    attendance_details_ids = fields.One2many("xe.attendance.details", "attendance_id")
    fetch_students = fields.Boolean(default=False)
    total_student_present = fields.Integer("Students Present")
    total_student_absent = fields.Integer("Students Absent")
    total_student_late = fields.Integer("Late Present")
    total_student_half = fields.Integer("Half Day Present")
    attendance_register_id = fields.Many2one(
        "xe.attendance.register", "Attendance Register"
    )
    attendance_type = fields.Selection(
        [
            ("daily_1", "Daily One-time"),
            ("daily_2", "Morning and Afternoon"),
            ("subject_wise", "Subject-wise"),
        ],
        "Type of Attendance",
    )
    attendance_session = fields.Selection(
        [("morning", "Morning"), ("afternoon", "Afternoon")]
    )
    subject_id = fields.Many2one("xe.subject", "Subject")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.onchange("attendance_register_id")
    def _set_attendance_type(self):
        for line in self:
            attendance_type = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("xe_attendance_management.attendance_type")
            )
            line.attendance_type = attendance_type

    def submit(self):
        attendance_details_ids = self.attendance_details_ids
        self.total_student_present = len(
            attendance_details_ids.filtered(lambda d: d.attendance == "present")
        )
        self.total_student_absent = len(
            attendance_details_ids.filtered(lambda d: d.attendance == "absent")
        )
        self.teacher_user_id = self.env.user.id
        self.state = "submitted"

    def approve(self):
        self.state = "approved"

    def cancel_draft(self):
        self.state = "cancel"

    def cancel(self):
        self.state = "cancel"

    def reset_to_draft(self):
        self.state = "draft"

    def load_student_data(self):
        if self.attendance_details_ids:
            for line in self.attendance_details_ids:
                line.unlink()
        domain = []
        if self.attendance_register_id.course_id:
            domain.append(("course_id", "=", self.attendance_register_id.course_id.id))
        if self.attendance_register_id.class_room_id:
            domain.append(
                ("classroom_id", "=", self.attendance_register_id.class_room_id.id)
            )
        students = self.env["xe.student"].search(domain)
        vals = []
        for stud in students:
            line_vals = {}
            line_vals["student_id"] = stud.id
            line_vals["attendance_id"] = self.id
            vals.append((0, 0, line_vals))
        self.attendance_details_ids = vals
        self.fetch_students = True

    @api.constrains("attendance_date")
    def _check_records(self):
        current_date = date.today()
        no_of_records = self.env["xe.student.attendance"].search_count(
            [
                ("attendance_register_id", "=", self.attendance_register_id.id),
                ("attendance_date", "=", current_date),
            ]
        )
        if self.attendance_type == "daily_1" and no_of_records > 1:
            raise UserError(_("You cant create more than one attendance sheet/day"))
        if self.attendance_type == "daily_2" and no_of_records > 2:
            raise UserError(_("You cant create more than two attendance sheet/day"))
        if self.attendance_type == "subject_wise":
            sub_records = self.env["xe.student.attendance"].search_count(
                [
                    ("attendance_register_id", "=", self.attendance_register_id.id),
                    ("attendance_date", "=", current_date),
                    ("subject_id", "=", self.subject_id.id),
                ]
            )
            if sub_records > 1:
                raise UserError(
                    _(
                        "You cant create multiple attendance sheet/day for the same subject"
                    )
                )

    @api.model
    def create(self, vals):
        register = self.env["xe.attendance.register"].browse(
            vals.get("attendance_register_id")
        )
        name = register.code + "(" + str(vals.get("attendance_date")) + ")"
        if (
            vals.get("attendance_type") == "daily_2"
            and vals.get("attendance_session") == "morning"
        ):
            name += " Morning Session"
        if (
            vals.get("attendance_type") == "daily_2"
            and vals.get("attendance_session") == "afternoon"
        ):
            name += " Afternoon Session"
        if vals.get("subject_id"):
            subject_name = self.env["xe.subject"].browse(vals.get("subject_id")).name
            if subject_name:
                name += " " + subject_name
            if vals.get("teacher_user_id"):
                user = self.env["res.users"].browse(vals.get("teacher_user_id")).name
                name += " " + user
        vals["name"] = name
        result = super(AttendanceManagement, self).create(vals)
        result.load_student_data()
        return result

    def refresh(self):
        self.load_student_data()

    @api.model
    def create_attendance_sheet_crone(self):
        config_param_obj = self.env["ir.config_parameter"].sudo()
        student_attendance_obj = self.env["xe.student.attendance"]
        attendance_type = config_param_obj.get_param(
            "xe_attendance_management.attendance_type"
        )
        days_list = []
        sunday_bool = config_param_obj.get_param("xe_attendance_management.sunday_bool")
        if sunday_bool:
            days_list.append("Sunday")
        monday_bool = config_param_obj.get_param("xe_attendance_management.monday_bool")
        if monday_bool:
            days_list.append("Monday")
        tuesday_bool = config_param_obj.get_param(
            "xe_attendance_management.tuesday_bool"
        )
        if tuesday_bool:
            days_list.append("Tuesday")
        wednesday_bool = config_param_obj.get_param(
            "xe_attendance_management.wednesday_bool"
        )
        if wednesday_bool:
            days_list.append("Wednesday")
        thursday_bool = config_param_obj.get_param(
            "xe_attendance_management.thursday_bool"
        )
        if thursday_bool:
            days_list.append("Thursday")
        friday_bool = config_param_obj.get_param("xe_attendance_management.friday_bool")
        if friday_bool:
            days_list.append("Friday")
        saturday_bool = config_param_obj.get_param(
            "xe_attendance_management.saturday_bool"
        )
        if saturday_bool:
            days_list.append("Saturday")
        if attendance_type:
            company_ids = self.env["res.company"].search([]).ids
            current_date = str(datetime.now())[:10]
            for company in company_ids:
                attendance_registers = self.env["xe.attendance.register"].search(
                    [("company_id", "=", company), ("code", "!=", False)]
                )
                if len(attendance_registers) < 1:
                    _logger.info(company)
                    _logger.info(
                        "No attendance Register Found, please create an"
                        " attendance register first then execute this Cron"
                    )
                current_day = datetime.now().strftime("%A")
                if current_day in days_list:
                    for recd in attendance_registers:
                        created_sheets = student_attendance_obj.search_count(
                            [
                                ("attendance_register_id", "=", recd and recd.id),
                                ("attendance_date", "=", current_date),
                                ("company_id", "=", company),
                            ]
                        )
                        if attendance_type == "daily_1" and created_sheets == 0:
                            name = (
                                "Attendance of "
                                + recd.code
                                + "("
                                + str(current_date)
                                + ")"
                            )
                            vals = {
                                "attendance_register_id": recd.id,
                                "attendance_date": current_date,
                                "attendance_type": attendance_type,
                                "name": name,
                                "company_id": company,
                            }
                            student_attendance_obj.create(vals)
                        if attendance_type == "daily_2" and created_sheets < 2:
                            name = recd.code + "(" + str(current_date) + ")"
                            vals = {
                                "attendance_register_id": recd.id,
                                "attendance_date": current_date,
                                "attendance_type": attendance_type,
                                "company_id": company,
                            }
                            if created_sheets == 0:
                                name += "Morning Session"
                                vals["attendance_session"] = "morning"
                                vals["name"] = name
                                student_attendance_obj.create(vals)
                                vals["name"] = (
                                    recd.code
                                    + "("
                                    + str(current_date)
                                    + ")"
                                    + "Afternoon Session"
                                )
                                vals["attendance_session"] = "afternoon"
                                student_attendance_obj.create(vals)
                            else:
                                created_sheet = self.env[
                                    "xe.student.attendance"
                                ].search(
                                    [
                                        ("attendance_register_id", "=", recd.id),
                                        ("attendance_date", "=", current_date),
                                        ("company_id", "=", company),
                                    ]
                                )
                                if created_sheet.attendance_session == "morning":
                                    name += "Afternoon Session"
                                else:
                                    name += "Morning Session"
                                vals["attendance_session"] = "afternoon"
                                vals["name"] = name
                                student_attendance_obj.create(vals)
                        if attendance_type == "subject_wise":
                            created_session_sheets = self.env[
                                "xe.session.lines"
                            ].search(
                                [
                                    ("course_id", "=", recd.course_id.id),
                                    ("session_date", "=", current_date),
                                    ("company_id", "=", company),
                                ]
                            )
                            for session in created_session_sheets:
                                sheet_count = student_attendance_obj.search_count(
                                    [
                                        ("attendance_register_id", "=", recd.id),
                                        ("subject_id", "=", session.subject_id.id),
                                        ("attendance_date", "=", current_date),
                                        ("company_id", "=", company),
                                    ]
                                )
                                if sheet_count == 0:
                                    name = (
                                        recd.code
                                        + "("
                                        + str(current_date)
                                        + ") "
                                        + session.subject_id.name
                                    )
                                    vals = {
                                        "attendance_register_id": recd.id,
                                        "attendance_date": current_date,
                                        "attendance_type": attendance_type,
                                        "subject_id": session.subject_id.id,
                                        "name": name,
                                        "company_id": company,
                                    }
                                    student_attendance_obj.create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Confirmed/Approved records cannot be deleted"))
        return super(AttendanceManagement, self).unlink()

    def get_total_data(self, last_attendance, report_data):
        if "course_id" in report_data:
            course_id = int(report_data["course_id"])
        if "class_room_id" in report_data:
            class_room_id = int(report_data["class_room_id"])

        domain = [
            ("state", "not in", ["draft", "cancel"]),
            ("attendance_date", "=", last_attendance),
        ]
        if course_id:
            domain.append(("attendance_register_id.course_id", "=", course_id))
        if class_room_id:
            domain.append(("attendance_register_id.class_room_id", "=", class_room_id))
        attendance_data = self.env["xe.student.attendance"].search(domain)
        attendance_type = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_attendance_management.attendance_type")
        )
        if attendance_type == "daily_2":
            data_dict = {
                "total_students": 0,
                "total_present_morning": 0,
                "total_absent_morning": 0,
                "total_present_afternoon": 0,
                "total_absent_afternoon": 0,
            }
        else:
            data_dict = {"total_students": 0, "total_present": 0, "total_absent": 0}
        data_dict["attendance_type"] = attendance_type
        total_students = 0
        attendance_sheets = []
        for data in attendance_data:
            if data.attendance_type == "daily_2":
                unique_name = (
                    data.attendance_register_id.name
                    + data.attendance_date.strftime("%d-%m-%Y")
                )
                if unique_name not in attendance_sheets:
                    attendance_sheets.append(unique_name)
                    total_students = len(data.attendance_details_ids)
                    data_dict["total_students"] += total_students
                if data.attendance_session == "morning":
                    data_dict["total_present_morning"] += data.total_student_present
                    data_dict["total_absent_morning"] += data.total_student_absent
                else:
                    data_dict["total_present_afternoon"] += data.total_student_present
                    data_dict["total_absent_afternoon"] += data.total_student_absent
            if data.attendance_type == "daily_1":
                data_dict["total_students"] += len(data.attendance_details_ids)
                data_dict["total_present"] += data.total_student_present
                data_dict["total_absent"] += data.total_student_absent
        return data_dict


class RemarksType(models.Model):
    _name = "xe.remarks.type"
    _description = "Remarks Type"

    name = fields.Char("Remarks")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )


class StudentAttendanceDetails(models.Model):
    _name = "xe.attendance.details"
    _description = "Student Attendance Details"

    def _get_remarks_type(self):
        remarks_type = self.env.ref("xe_attendance_management.remark_type_default")
        return remarks_type

    student_id = fields.Many2one("xe.student")
    roll_number = fields.Char("Admission Number", related="student_id.roll_number")
    attendance = fields.Selection(
        [("present", "Present"), ("absent", "Absent")], default="present"
    )
    remarks = fields.Text()
    attendance_id = fields.Many2one(
        "xe.student.attendance", "Attendance", ondelete="cascade"
    )
    course_id = fields.Many2one(
        "xe.course",
        string="Class",
        related="attendance_id.attendance_register_id.course_id",
    )
    class_room_id = fields.Many2one(
        "xe.classroom",
        string="Class",
        related="attendance_id.attendance_register_id.class_room_id",
    )
    term_id = fields.Many2one("xe.term", "Term", related="attendance_id.term_id")
    attendance_date = fields.Date(related="attendance_id.attendance_date")
    remarks_type_id = fields.Many2one(
        "xe.remarks.type", "Remarks", default=_get_remarks_type
    )
    company_id = fields.Many2one(
        "res.company", string="Company", related="attendance_id.company_id", store=True
    )

    def write(self, vals):
        default_remarks = self.env.ref(
            "xe_attendance_management.remark_type_default"
        ).id
        attendance_value = vals.get("attendance")

        if attendance_value == "present":
            vals["remarks_type_id"] = default_remarks
        elif attendance_value is not None and attendance_value != "present":
            vals.setdefault("remarks_type_id", default_remarks)
        elif "remarks_type_id" in vals and self.attendance == "present":
            vals["remarks_type_id"] = default_remarks

        return super(StudentAttendanceDetails, self).write(vals)
