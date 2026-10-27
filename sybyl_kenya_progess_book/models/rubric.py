from odoo import api, _, models, fields


class XeRubric(models.Model):
    _name = "xe.rubric"
    _rec_name = "code"

    name = fields.Text()
    code = fields.Char(string="Rubric ID")
    substrand_id = fields.Many2one("xe.substrand")
    strand_id = fields.Many2one("xe.strand", related="substrand_id.strand_id")
    theme_id = fields.Many2one("xe.theme", related="strand_id.theme_id")
    subject_id = fields.Many2one("xe.subject")
    term_id = fields.Many2one("xe.academic.terms", related="substrand_id.term_id")
    activity = fields.Text()
    subject_from = fields.Selection([("theme", "Theme"), ("strand", "Strand")])

    @api.model
    def create(self, vals):
        res = super(XeRubric, self).create(vals)
        res.name = res.substrand_id.name
        return res

    def write(self, vals):
        res = super(XeRubric, self).write(vals)
        if vals.get("substrand_id"):
            self.name = self.substrand_id.name
        return res

    @api.onchange("substrand_id")
    def _onchange_substrand_id(self):
        if self.substrand_id:
            if self.theme_id and self.theme_id.subject_id:
                self.subject_id = self.theme_id.subject_id
                self.subject_from = "theme"
            elif (
                self.strand_id
                and self.strand_id.subject_id
                and not self.theme_id.subject_id
            ):
                self.subject_id = self.strand_id.subject_id
                self.subject_from = "strand"
            else:
                self.subject_id = False
