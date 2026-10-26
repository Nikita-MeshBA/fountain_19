from odoo import models, fields, api


class ExamAnalysisWizard(models.TransientModel):
    _name = "exam.analysis.report.wizard"
    _rec_name = "name"
    _description = "Exam Analysis Report"

    name = fields.Char("Student Attendance Report", default="Exam Anaylsis Report")
    analysis_type = fields.Selection(
        [
            ("exam_session_wise", "Exam Session"),
            ("subject_wise", "Subject Wise"),
        ],
        string="Exam Analysis Type",
        default="exam_session_wise",
        tracking=True,
    )
    exam_session_id = fields.Many2one("xe.exam.session", string="Exam Session")
    exam_ids = fields.Many2many(
        "xe.exam", "exam_analysis_rel", "exam_id", "report_id", string="Exam"
    )
    subject_ids = fields.Many2many(
        "xe.subject",
        "subject_analysis_rel",
        "subject_id",
        "report_id",
        string="Subject",
    )
    type = fields.Selection(
        [("class", "Class"), ("classroom", "Classroom")], default="class"
    )
    course_id = fields.Many2one("xe.course", "Class")
    classroom_ids = fields.Many2many("xe.classroom")

    @api.onchange("analysis_type", "exam_session_id")
    def _set_domain(self):
        domain = {}
        if self.analysis_type and self.exam_session_id:
            exam_session_id = self.exam_session_id
            if self.analysis_type == "exam_session_wise":
                domain = {
                    "domain": {
                        "exam_ids": [
                            ("session_id", "=", exam_session_id.id),
                            ("state", "=", "done"),
                        ]
                    }
                }
            if self.analysis_type == "subject_wise":
                exam_ids = exam_session_id.exam_ids.filtered(
                    lambda d: d.state == "done"
                )
                subject_ids = exam_ids.mapped("subject_id")
                domain = {"domain": {"subject_id": [("id", "=", subject_ids)]}}
        return domain

    def print_analysis_report_excel(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "company": self.exam_session_id.company_id.id,
            "report_name": self.exam_session_id.name,
            "form": {
                "course_id": self.course_id.id if self.course_id else False,
                "classroom_ids": (
                    self.classroom_ids.ids if self.classroom_ids else False
                ),
                "analysis_type": self.analysis_type,
                "subject_ids": self.subject_ids.ids,
                "exam_ids": self.exam_ids.ids,
                "session_id": self.exam_session_id.id,
                "session_name": self.exam_session_id.name,
            },
        }
        # print(data)
        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref(
            "xe_exam_management.exam_analysis_report_xlsx"
        ).report_action(self, data=data)
