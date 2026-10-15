from odoo import models, fields


class LeavingCertificateAttributes(models.Model):
    _name = "leave.certificate.attribute"
    _inherit = ["mail.thread"]
    _description = "Leaving Certificate Attribute"

    name = fields.Char("Attribute", required=True, tracking=True)
