# -*- coding: utf-8 -*-
import time

from odoo import models, fields, api


class ReportTicket(models.AbstractModel):
    _name = "report.xe_exam_management.report_ticket"
    _description = "Exam Management Report Ticket"

    def get_date(self, exam_line):
        timestamp = fields.Datetime.context_timestamp
        dt = fields.Datetime
        schedule_start = timestamp(self, dt.from_string(exam_line.start_time))
        schedule_end = timestamp(self, dt.from_string(exam_line.end_time))
        schedule_start = fields.Datetime.to_string(schedule_start)
        schedule_end = fields.Datetime.to_string(schedule_end)
        return schedule_start[11:] + " To " + schedule_end[11:]

    def get_subject(self, exam_session):
        lst = []
        for exam_line in exam_session["exam_ids"]:
            res1 = {
                "subject": exam_line.subject_id.name,
                "date": str(exam_line.start_time)[:10],
                "time": self.get_date(exam_line),
                "sup_sign": "",
            }
            lst.append(res1)
        return lst

    def get_data(self, data):
        final_lst = []
        exam_session = self.env["xe.exam.session"].browse(data["exam_session_id"][0])
        student_search = self.env["xe.student"].search(
            [("course_detail_ids.course_id", "=", exam_session.course_id.id)]
        )
        for student in student_search:
            student_course = self.env["xe.student.course"].search(
                [
                    ("student_id", "=", student.id),
                    ("course_id", "=", exam_session.course_id.id),
                ]
            )
            res = {
                "exam": exam_session.name,
                "exam_code": exam_session.exam_code,
                "course": exam_session.course_id.name,
                "student": student.name,
                "image": student.image_256,
                "roll_number": student_course.roll_number,
                "line": self.get_subject(exam_session),
            }
            final_lst.append(res)
        return final_lst

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model")
        if model:
            docs = self.env[model].browse(self.env.context.get("active_id"))
        if not model:
            docs = self.env["student.hall.ticket"].create(
                {"exam_session_id": data["exam_session_id"][0]}
            )
        docargs = {
            "doc_ids": self.ids,
            "doc_model": model,
            "docs": docs,
            "time": time,
            "get_data": self.get_data(data),
            "res_company": self.env.user.company_id,
        }
        return docargs
