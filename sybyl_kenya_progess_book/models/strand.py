from odoo import api, _, models, fields


class XeStrand(models.Model):
    _name = "xe.strand"

    code = fields.Char(string="Strand ID")
    name = fields.Text(string="Strand Name")
    theme_id = fields.Many2one("xe.theme", string="Theme")
    subject_id = fields.Many2one("xe.subject", domain=[("is_theme", "=", False)])
    substrand_ids = fields.One2many("xe.substrand", "strand_id", string="Substrands")
    student_ids = fields.Many2many("xe.student", string="Students")
