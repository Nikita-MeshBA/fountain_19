# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class AdmissionEnquiryForm(models.Model):
    _inherit = "xe.admission.enquiry"

    doc_type = fields.Selection(
        [
            ("online", "Online"),
            ("system", "System"),
        ],
        string="Generated Through",
        default="system",
    )
