from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def get_marksheet_lines(self):
        ids = []
        marksheet_lines = self.env["xe.marksheet.line"].search([])
        for line in marksheet_lines:
            exams = line.marksheet_reg_id.exam_session_id.exam_ids.filtered(
                lambda l: l.staff_id.user_id.id == self.env.user.id
            )
            if exams and exams.classroom_ids:
                ids += exams.classroom_ids.ids

        if ids:
            ids = list(set(ids))
        return [("classroom_id", "in", ids)]
