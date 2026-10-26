import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class FeesType(models.Model):
    _name = "xe.fees.type"
    _description = "Fees Type Form"
    _rec_name = "fee_type"

    @api.model
    def create(self, vals):
        result = super(FeesType, self).create(vals)
        if result.type == "transport":
            result.is_transport_fees = True
            result.is_academic = result.is_optional = result.is_activity = False
        elif result.type == "academic":
            result.is_academic = True
            result.is_transport_fees = result.is_optional = result.is_activity = False
        elif result.type == "activity":
            result.is_activity = True
            result.is_academic = result.is_optional = result.is_transport_fees = False
        elif result.type == "optional":
            result.is_optional = True
            result.is_academic = result.is_activity = result.is_transport_fees = False
        else:
            result.is_academic = result.is_transport_fees = result.is_activity = False

        fee_type = result.fee_type
        product_template_obj = self.env["product.template"]
        product = product_template_obj.sudo().search(
            [
                ("name", "=", fee_type),
                ("is_fee", "=", True),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if not product:
            product = product_template_obj.create(
                {
                    "name": fee_type,
                    "is_fee": True,
                    "detailed_type": "service",
                    "company_id": self.env.company.id,
                }
            )
        result.sudo().write({"product_id": product.id, "fee_type": fee_type})
        return result

    def write(self, values):
        if "fee_type" in values:
            fee_type = values["fee_type"]
            product_template_obj = self.env["product.template"]
            product = product_template_obj.sudo().search(
                [
                    ("name", "=", fee_type),
                    ("is_fee", "=", True),
                    ("company_id", "=", self.env.company.id),
                ],
                limit=1,
            )
            if not product:
                product = product_template_obj.create(
                    {"name": fee_type, "is_fee": True, "detailed_type": "service"}
                )

            values["product_id"] = product.id
        result = super(FeesType, self).write(values)
        return result

    fee_type = fields.Char(required=True, store=True)
    product_id = fields.Many2one("product.template")
    fee = fields.Boolean(default=True)
    duration = fields.Selection(
        [
            ("recurring", "Recurring"),
            # ("onetime", "One-Time"),
            ("admissiontime", "Admission-Time"),
        ],
        default="recurring",
    )
    type = fields.Selection(
        [
            ("academic", "Academic Fees"),
            ("transport", "Transport Fees"),
            ("activity", "Activity Fees"),
            ("optional", "Optional Fees"),
        ],
        default="academic",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    is_transport_fees = fields.Boolean()
    is_academic = fields.Boolean(string="Is Academic Fees")
    is_activity = fields.Boolean(string="Is Activity Fees")
    is_boarding = fields.Boolean(string="Is Boarding Fees", default=False)
    is_optional = fields.Boolean(string="Is Optional Fees")
    description = fields.Text()

    @api.onchange("fee_type", "type")
    def onchange_fees_type(self):
        if self.fee_type:
            product_template_obj = self.env["product.template"]
            product = product_template_obj.sudo().search(
                [
                    ("name", "=", self.fee_type),
                    ("is_fee", "=", True),
                    ("company_id", "=", self.env.company.id),
                ],
                limit=1,
            )
            if not product:
                product = product_template_obj.create(
                    {
                        "name": self.fee_type,
                        "is_fee": True,
                        "detailed_type": "service",
                        "company_id": self.company_id.id,
                    }
                )

            self.product_id = product and product.id or False
            self.company_id = product.company_id.id
            self.fee_type = product and product.name or ""
            if self.type == "transport":
                self.type = "transport"
                self.is_transport_fees = True
            product.product_variant_id.is_fee_product = self.fee

        if self.type == "transport":
            self.is_transport_fees = True
            self.is_academic = self.is_activity = self.is_optional = False
        elif self.type == "academic":
            self.is_academic = True
            self.is_transport_fees = self.is_activity = self.is_optional = False
        elif self.type == "activity":
            self.is_activity = True
            self.is_academic = self.is_transport_fees = self.is_optional = False
        elif self.type == "optional":
            self.is_optional = True
            self.is_academic = self.is_activity = self.is_transport_fees = False
        else:
            self.is_academic = self.is_transport_fees = self.is_activity = (
                self.is_optional
            ) = False
