from datetime import datetime
from odoo import models, fields, api


class AddExamWizard(models.TransientModel):
    _name = "add.exam.wizard"

    session_id = fields.Many2one("xe.exam.session")
    class_id = fields.Many2one("xe.course")
    classroom_ids = fields.Many2many("xe.classroom")
    subject_ids = fields.Many2many("xe.subject")
    start_date = fields.Date()
    end_date = fields.Date()
    new_subject_ids = fields.Many2many("xe.subject", "new_add_exam_subject_id_rel")

    def add_new_exam(self):
        exam_lines = []
        for classroom in self.classroom_ids:
            for subject in self.subject_ids:
                if subject.is_examinable:
                    start_date = datetime.combine(self.start_date, datetime.min.time())
                    end_date = datetime.combine(self.end_date, datetime.min.time())
                    exam_vals = {
                        "name": self.session_id.name + "/" + subject.name,
                        "exam_code": self.session_id.exam_code + "/" + subject.code + "/" + classroom.code,
                        "classroom_ids": [(6, 0, [classroom.id])],
                        "subject_id": subject.id,
                        "start_time": start_date,
                        "end_time": end_date,
                        "total_marks": 1,
                        "min_marks": 1,
                    }
                    if self.session_id.staff_id:
                        exam_vals["staff_id"] = self.session_id.staff_id.id
                    exam_lines.append([0, 0, exam_vals])
        self.session_id.write({"exam_ids": exam_lines})