import datetime
import logging
from datetime import datetime, date

from odoo.exceptions import UserError

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AttendanceRegister(models.Model):
    _inherit = "xe.attendance.register"

    is_attendance_subject_wise = fields.Boolean(
        "Subject Wise Attendance", related="course_id.is_attendance_subject_wise"
    )


class AttendanceSheet(models.Model):
    _inherit = "xe.student.attendance"

    course_id = fields.Many2one("xe.course", related="attendance_register_id.course_id")
    is_attendance_subject_wise = fields.Boolean(
        "Subject Wise Attendance",
        related="attendance_register_id.course_id.is_attendance_subject_wise",
    )

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
        if self.is_attendance_subject_wise:
            if self.subject_id and self.subject_id.subject_mode == "yes":
                domain.append(("elective_subjects_ids", "in", [self.subject_id.id]))
            if self.subject_id and self.subject_id.subject_mode == "no":
                domain.append(("mandatory_subjects_ids", "in", [self.subject_id.id]))
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
        if (
                not self.is_attendance_subject_wise
                and self.attendance_type == "daily_1"
                and no_of_records > 1
        ):
            raise UserError(_("You cant create more than one attendance sheet/day"))
        if (
                not self.is_attendance_subject_wise
                and self.attendance_type == "daily_2"
                and no_of_records > 2
        ):
            raise UserError(_("You cant create more than two attendance sheet/day"))
        if self.is_attendance_subject_wise or self.attendance_type == "subject_wise":
            sub_records = self.env["xe.student.attendance"].search_count(
                [
                    ("attendance_register_id", "=", self.attendance_register_id.id),
                    ("attendance_date", "=", current_date),
                    ("subject_id", "=", self.subject_id.id),
                    ("teacher_user_id", "=", self.teacher_user_id.id),
                ]
            )
            if sub_records > 1:
                raise UserError(
                    _(
                        "You cant create multiple attendance sheet/day for the same subject"
                    )
                )

    @api.model
    def create_attendance_sheet_crone(self):
        student_attendance_obj = self.env["xe.student.attendance"]
        config_param_obj = self.env["ir.config_parameter"].sudo()
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
            current_day = datetime.now().strftime("%A")
            if current_day in days_list:
                for company in company_ids:
                    attendance_registers = self.env["xe.attendance.register"].search(
                        [("company_id", "=", company)]
                    )
                    if len(attendance_registers) < 1:
                        _logger.info(company)
                        _logger.info(
                            "No attendance Register Found, please create an "
                            "attendance register first then execute this Cron"
                        )
                    for recd in attendance_registers:
                        is_attendance_subject_wise = (
                            recd.course_id.is_attendance_subject_wise
                        )
                        created_sheets = student_attendance_obj.search_count(
                            [
                                ("attendance_register_id", "=", recd and recd.id),
                                ("attendance_date", "=", current_date),
                                ("company_id", "=", company),
                            ]
                        )
                        if (
                                not is_attendance_subject_wise
                                and attendance_type == "daily_1"
                                and created_sheets == 0
                        ):
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
                        if (
                                not is_attendance_subject_wise
                                and attendance_type == "daily_2"
                                and created_sheets < 2
                        ):
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
                                created_sheet = student_attendance_obj.search(
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
                        if is_attendance_subject_wise:
                            subjects = recd.course_id.course_subject_line_ids
                            for subject in subjects:
                                teachers = self.env["hr.employee"].search(
                                    [
                                        ("teach_type", "=", "teaching"),
                                        ("subject_ids.subject_ids", "in", [subject.id]),
                                    ]
                                )
                                for teacher in teachers:
                                    sheet_count = student_attendance_obj.search_count(
                                        [
                                            ("attendance_register_id", "=", recd.id),
                                            ("subject_id", "=", subject.id),
                                            (
                                                "teacher_user_id",
                                                "=",
                                                teacher.user_id.id,
                                            ),
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
                                                + subject.name
                                        )
                                        vals = {
                                            "attendance_register_id": recd.id,
                                            "attendance_date": current_date,
                                            "attendance_type": attendance_type,
                                            "subject_id": subject.id,
                                            "name": name,
                                            "company_id": company,
                                            "teacher_user_id": teacher.user_id.id,
                                        }
                                        student_attendance_obj.create(vals)
