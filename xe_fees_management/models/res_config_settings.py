from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_transport = fields.Boolean(config_parameter="xe_fees_management.is_transport")
    is_activity = fields.Boolean(config_parameter="xe_fees_management.is_activity")
    is_boarding = fields.Boolean(config_parameter="xe_fees_management.is_boarding")
    is_optional = fields.Boolean(config_parameter="xe_fees_management.is_optional")
    interview_fee_type = fields.Selection(
        [
            ("no", "No Interview Fees"),
            ("general", "General Interview Fees"),
            ("class_wise", "Interview Fees Class Wise"),
        ],
        default="no",
    )
    gen_interview_pdt_id = fields.Many2one(
        "product.product",
        string="Interview Fee Product",
        config_parameter="xe_fees_management.gen_interview_pdt_id",
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        is_transport = params.get_param(
            "xe_fees_management.is_transport", default=False
        )
        is_activity = params.get_param("xe_fees_management.is_activity", default=False)
        is_boarding = params.get_param("xe_fees_management.is_boarding", default=False)
        is_optional = params.get_param("xe_fees_management.is_optional", default=False)
        interview_fee_type = params.get_param(
            "xe_fees_management.interview_fee_type", default=False
        )

        res.update(
            is_transport=is_transport,
            is_activity=is_activity,
            is_boarding=is_boarding,
            is_optional=is_optional,
            interview_fee_type=interview_fee_type,
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "xe_fees_management.is_transport", self.is_transport
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xe_fees_management.is_activity", self.is_activity
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xe_fees_management.is_boarding", self.is_boarding
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xe_fees_management.is_optional", self.is_optional
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xe_fees_management.interview_fee_type",
            self.interview_fee_type,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xe_fees_management.gen_interview_pdt_id",
            self.gen_interview_pdt_id.id,
        )
