from odoo import models, fields


class ConfirmExam(models.TransientModel):
    _name = "exam.confirm.wizard"

    name = fields.Char()
    exam_session_id = fields.Many2one("xe.exam.session")

    def action_ok(self):
        self.exam_session_id.create_exams_new()
