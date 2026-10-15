from odoo import fields, models


class AdmissionFeeWizard(models.Model):
    _name = "clearance.form.attributes"
    _description = "clearance form attributes"

    name = fields.Char()
    section = fields.Selection(
        [("part_a", "Part A"), ("part_b", "Part B")], default="part_a"
    )
