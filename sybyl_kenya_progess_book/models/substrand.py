from odoo import api, _, models, fields


class XeSubstrand(models.Model):
    _name = "xe.substrand"

    code = fields.Char(string="Subtrand ID")
    name = fields.Text(string="Substrand Name", required=True)
    strand_id = fields.Many2one("xe.strand")
    theme_id = fields.Many2one("xe.theme")
    subject_id = fields.Many2one("xe.subject")
    term_id = fields.Many2one("xe.academic.terms", string="Term")
    # student_ids = fields.Many2many("xe.student", string="Students")
    rubric_ids = fields.One2many("xe.rubric", "name", "Rubric")
    performance_indicator = fields.Char()

    # rubric_name = fields.Text(related="rubrics.activity", string="Activity")

    @api.onchange("strand_id")
    def _onchange_strand_id(self):
        if self.strand_id:
            if self.strand_id.theme_id:
                self.theme_id = self.strand_id.theme_id.id
                if self.strand_id.theme_id.subject_id:
                    self.subject_id = self.strand_id.theme_id.subject_id.id
                elif self.strand_id.subject_id:
                    self.subject_id = self.strand_id.subject_id.id
                else:
                    self.subject_id = False
            elif self.strand_id.subject_id:
                self.subject_id = self.strand_id.subject_id.id
            else:
                self.subject_id = False
