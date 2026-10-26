from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class AcademicTerms(models.Model):
    _inherit = "xe.academic.terms"

    next_term_open_date = fields.Date()

    @api.constrains("end_date", "next_term_open_date")
    def date_constrains(self):
        for rec in self:
            if rec.next_term_open_date and rec.next_term_open_date < rec.end_date:
                raise ValidationError(
                    _("Opening Date of Next Term should greater than End Date...")
                )
