from odoo import models, fields


class ExamAttendeeWizard(models.TransientModel):
    _name = "exam.attendee.report.wizard"

    name = fields.Char("Student Attendance Report", default="Exam Attendee Report")
    exam_id = fields.Many2one("xe.exam")

    def print_attendance_report_excel(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {"exam_id": self.exam_id.id},
        }
        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref(
            "xe_exam_management.exam_attendee_report_xlsx"
        ).report_action(self, data=data)
