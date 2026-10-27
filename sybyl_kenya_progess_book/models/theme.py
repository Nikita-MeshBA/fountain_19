from odoo import api, _, models, fields


class XeTheme(models.Model):
    _name = "xe.theme"

    name = fields.Text(string="Theme Name")
    code = fields.Char(string="Theme ID")
    subject_id = fields.Many2one("xe.subject")
    strand_ids = fields.One2many("xe.strand", "theme_id")
    student_ids = fields.Many2many("xe.student")
