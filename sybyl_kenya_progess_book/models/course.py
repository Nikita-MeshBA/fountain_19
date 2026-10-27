from odoo import models, fields, api, _


class CourseDetails(models.Model):
    _inherit = "xe.course"

    progress_book_pdf_format = fields.Selection(
        [("format1", "Format 1"), ("format2", "Format 2")], default="format1"
    )
