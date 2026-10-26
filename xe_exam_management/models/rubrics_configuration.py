from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class XeRubricsConfiguration(models.Model):
    _name = "xe.rubrics.configuration"

    min_per = fields.Integer("Minimum Marks")
    max_per = fields.Integer("Maximum Marks")
    name = fields.Char("Description")
    code = fields.Char()
    points = fields.Integer()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    exam_session_id = fields.Many2one("xe.exam.session")
    course_id = fields.Many2one(related="exam_session_id.course_id")
    subject_id = fields.Many2one("xe.subject")
    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
    sequence = fields.Integer()
    # old field
    new_code = fields.Many2one("xe.rubrics.code", string="Code")
    # new field
    new_code_id = fields.Many2one("xe.rubrics.code", string="Code")

    @api.onchange("new_code_id")
    def _set_name(self):
        for record in self:
            if record.new_code_id:
                record.name = record.new_code_id.name

    @api.constrains("code", "company_id")
    def check_code(self):
        for record in self:
            if record.code:
                rubrics_configuration_ids = self.search(
                    [
                        ("code", "=", record.code),
                        ("company_id", "=", record.company_id.id),
                    ]
                )
                if len(rubrics_configuration_ids) > 1:
                    raise ValidationError(_("Code unique per company"))

    @api.constrains("min_per", "max_per")
    def mark_check(self):
        for rec in self:
            if rec.min_per and rec.max_per and int(rec.min_per) > int(rec.max_per):
                raise ValidationError(
                    "'Maximum Mark' must be greater than 'Minimum Mark'"
                )
