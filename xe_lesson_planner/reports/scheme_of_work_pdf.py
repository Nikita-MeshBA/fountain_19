# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import api, fields, models, _


class ReportSchemeOfWork(models.AbstractModel):
    _name = "report.xe_lesson_planner.report_schme_of_work_pdf"
    _description = "Scheme Of Work Analysis Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model")
        docs = self.env[model].browse(self.env.context.get("active_id"))
        date = str(datetime.now()).split(".")[0]
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        if data.get("fees_filter") == "employee":
            employee_id = self.env["hr.employee"].browse([data["employee"]])
            data["employee"] = employee_id.name
            domain = [("employee_id", "=", employee_id.id)]
            if date_from and date_to:
                domain += [
                    ("create_date", ">=", date_from),
                    ("create_date", "<=", date_to),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)
        elif data.get("fees_filter") == "department":
            department_id = self.env["hr.department"].browse([data["department"]])
            data["department"] = department_id.name
            domain = [("department_id", "=", department_id.id)]
            if date_from and date_to:
                domain += [
                    ("create_date", ">=", date_from),
                    ("create_date", "<=", date_to),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)
        elif data.get("fees_filter") == "classroom":
            domain = [("classroom_id", "in", data["classroom"])]
            if date_from and date_to:
                domain += [
                    ("create_date", ">=", date_from),
                    ("create_date", "<=", date_to),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)
        elif data.get("fees_filter") == "course" and data["course"]:
            domain = [("class_id", "in", data["course"])]
            if date_from and date_to:
                domain += [
                    ("create_date", ">=", date_from),
                    ("create_date", "<=", date_to),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)

        final_result = []
        for s in scheme_of_work_rec:
            subject = ""
            sub_name_list = s.assigned_sub_ids.mapped("name")
            for i in range(0, len(sub_name_list)):
                subject = " " + subject + sub_name_list[i] + ","
            vals = {
                "name": s.employee_id.name,
                "school": s.company_id.name,
                "subjects": subject,
                "period_per_week": s.period_per_week,
                "department_head_id": s.department_head_id.name,
                "head_teacher_id": s.head_teacher_id.name,
                "line_ids": s.scheme_of_work_ids,
            }
            final_result.append(vals)

        return {
            "doc_ids": self.ids,
            "doc_model": model,
            "data": data,
            "date": date,
            "docs": docs,
            "time": time,
            "get_details": final_result,
        }
