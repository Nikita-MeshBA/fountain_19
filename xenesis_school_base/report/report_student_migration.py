# -*- coding: utf-8 -*-
import time
from datetime import datetime

from odoo.exceptions import UserError

from odoo import api, models, _


class ReportStudentMigration(models.AbstractModel):
    _name = "report.xenesis_school_base.report_studentmigration"
    _description = "Student Migration Report"

    def _get_report_details(self, date_from, date_to, mode, ids):
        result = []
        if mode == "Student":
            migration_history = self.env["xe.migration.history"].search(
                [
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                    ("student_id", "=", ids),
                ]
            )
            if not migration_history:
                raise UserError(
                    _(
                        "No records found for the above search condition!,"
                        " Check your search condition"
                    )
                )
            for line in migration_history:
                values = {
                    "date": line.date,
                    "user": line.user_id.name,
                    "remarks": line.remarks,
                    "roll_number": line.student_id.roll_number,
                    "from_course": line.from_course_id.name,
                    "to_course": line.to_course_id.name,
                    "from_term": line.from_term_id.name,
                    "to_term": line.to_term_id.name,
                    "student": line.student_id.name,
                }
                result.append(values)
        if mode == "Class":
            migration_history = self.env["xe.migration.history"].search(
                [
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                    ("to_course_id", "=", ids),
                ]
            )
            if not migration_history:
                raise UserError(
                    _(
                        "No records found for the above search condition!,"
                        " Check your search condition"
                    )
                )
            for line in migration_history:
                values = {
                    "date": line.date,
                    "user": line.user_id.name,
                    "remarks": line.remarks,
                    "roll_number": line.student_id.roll_number,
                    "from_course": line.from_course_id.name,
                    "to_course": line.to_course_id.name,
                    "from_term": line.from_term_id.name,
                    "to_term": line.to_term_id.name,
                    "student": line.student_id.name,
                }
                result.append(values)
        if mode == "Term":
            migration_history = self.env["xe.migration.history"].search(
                [
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                    ("to_term_id", "=", ids),
                ]
            )
            if not migration_history:
                raise UserError(
                    _(
                        "No records found for the above search condition!,"
                        " Check your search condition"
                    )
                )
            for line in migration_history:
                values = {
                    "date": line.date,
                    "user": line.user_id.name,
                    "remarks": line.remarks,
                    "roll_number": line.student_id.roll_number,
                    "from_course": line.from_course_id.name,
                    "to_course": line.to_course_id.name,
                    "from_term": line.from_term_id.name,
                    "to_term": line.to_term_id.name,
                    "student": line.student_id.name,
                }
                result.append(values)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        if (
            not data.get("form")
            or not self.env.context.get("active_model")
            or not self.env.context.get("active_id")
        ):
            raise UserError(
                _("Form content is missing, this report cannot be printed.")
            )
        model = self.env.context.get("active_model")
        docs = self.env[model].browse(self.env.context.get("active_id"))
        date_from = data["form"]["date_from"]
        date_to = data["form"]["date_to"]
        date = str(datetime.now()).split(".", 1)[0]
        final_result = []
        course_id = False
        term_id = False
        student_id = False
        variant_header = False
        variant_value = False
        if data["form"]["student_id"]:
            student_id = data["form"]["student_id"][0]
            ids = student_id
            variant_value = data["form"]["student_id"][1]
            variant_header = "Student"
            final_result = self._get_report_details(
                date_from, date_to, variant_header, ids
            )

        if data["form"]["course_id"]:
            course_id = data["form"]["course_id"][0]
            ids = course_id
            variant_value = data["form"]["course_id"][1]
            variant_header = "Class"
            final_result = self._get_report_details(
                date_from, date_to, variant_header, ids
            )
        if data["form"]["term_id"]:
            term_id = data["form"]["term_id"][0]
            ids = term_id
            variant_value = data["form"]["term_id"][1]
            variant_header = "Term"
            final_result = self._get_report_details(
                date_from, date_to, variant_header, ids
            )
        return {
            "doc_ids": self.ids,
            "doc_model": model,
            "data": data["form"],
            "date_from": date_from,
            "date": date,
            "date_to": date_to,
            "variant_value": variant_value,
            "variant_header": variant_header,
            "docs": docs,
            "time": time,
            "get_details": final_result,
        }
