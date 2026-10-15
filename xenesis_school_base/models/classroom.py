import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Classroom(models.Model):
    _name = "xe.classroom"
    _inherit = ["mail.thread"]
    _description = "Classroom"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    course_id = fields.Many2one("xe.course", string="Class")
    capacity = fields.Integer(string="Number of Person")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    teacher_id = fields.Many2one(
        "hr.employee", domain=[("teach_type", "=", "teaching")]
    )
    teacher_signature_html = fields.Binary()

    # _sql_constraints = [
    #     ("classroom_code_uniq", "unique (code)", "Code should be unique per classroom!")
    # ]

