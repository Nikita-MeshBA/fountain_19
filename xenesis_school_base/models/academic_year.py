import logging

from odoo.exceptions import ValidationError

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)


class AcademicYear(models.Model):
    _name = "xe.academic.year"
    _description = "Academic Year"

    name = fields.Char()
    code = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    terms_ids = fields.One2many("xe.academic.terms", "academic_year_id")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.constrains("end_date", "start_date")
    def date_constrains(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError(
                    _("Sorry, End Date Must be greater Than Start Date...")
                )


class AcademicTerms(models.Model):
    _name = "xe.academic.terms"
    _description = "Academic Terms"

    # old field
    academic_year = fields.Many2one("xe.academic.year")
    # new field
    academic_year_id = fields.Many2one("xe.academic.year")
    name = fields.Char()
    code = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    no_of_students = fields.Float()
    exam_type = fields.Selection(
        [("opener", "Opener Exam"), ("mid", "Mid Term Exam"), ("end", "End Term")],
        default="opener",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.constrains("end_date", "start_date")
    def date_constrains(self):
        for rec in self:
            if (
                not rec.academic_year_id.start_date <= rec.start_date
                and not rec.academic_year_id.end_date >= rec.end_date
            ):
                raise ValidationError(_("Sorry, Please enter the valid date..."))
