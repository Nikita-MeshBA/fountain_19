from datetime import date
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class FleetVehicleLogServicesInherit(models.Model):
    _inherit = "fleet.vehicle.log.services"

    product_id = fields.Many2one("product.product", tracking=True)
    product_description = fields.Char(tracking=True)
    move_id = fields.Many2one("account.move", tracking=True)
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        "Vehicle",
        required=True,
        help="Vehicle concerned by this log",
        tracking=True,
    )
    amount = fields.Monetary("Cost", tracking=True)
    description = fields.Char(tracking=True)
    odometer_id = fields.Many2one(
        "fleet.vehicle.odometer",
        "Odometer",
        help="Odometer measure of the vehicle at the moment of this log",
        tracking=True,
    )
    odometer = fields.Float(
        compute="_get_odometer",
        inverse="_set_odometer",
        string="Odometer Value",
        help="Odometer measure of the vehicle at the moment of this log",
        tracking=True,
    )
    odometer_unit = fields.Selection(
        related="vehicle_id.odometer_unit", string="Unit", readonly=True, tracking=True
    )
    date = fields.Date(
        help="Date when the cost has been executed",
        default=fields.Date.context_today,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company, tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", tracking=True
    )
    purchaser_id = fields.Many2one(
        "res.partner",
        string="Driver",
        compute="_compute_purchaser_id",
        readonly=False,
        store=True,
        tracking=True,
    )
    inv_ref = fields.Char("Vendor Reference", tracking=True)
    vendor_id = fields.Many2one("res.partner", "Vendor", tracking=True)
    notes = fields.Text(tracking=True)
    service_type_id = fields.Many2one(
        "fleet.service.type",
        "Service Type",
        required=True,
        default=lambda self: self.env.ref(
            "fleet.type_service_service_8", raise_if_not_found=False
        ),
        tracking=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("running", "Running"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        string="Stage",
        group_expand="_expand_states",
        tracking=True,
    )

    def _get_invoice_line_name(self):
        self.ensure_one()
        if self.product_description:
            product_desc = self.product_description
        elif self.product_id and self.product_id.description_purchase:
            product_desc = self.product_id.description_purchase
        else:
            product_desc = ""
        return product_desc

    def _get_account_id(self):
        self.ensure_one()
        account_id = False
        # if cost has product specified, get account from product settings
        if self.product_id:
            account_id = self.product_id.product_tmpl_id._get_product_accounts()[
                "expense"
            ]
        return account_id

    def _get_tax_ids(self, fiscal_position_id=None):
        self.ensure_one()
        taxes = False
        if self.product_id:
            taxes = self.product_id.supplier_taxes_id.filtered(
                lambda r: not self.company_id or r.company_id == self.company_id
            )
        if fiscal_position_id and taxes:
            taxes = fiscal_position_id.map_tax(taxes)
        return taxes

    def _prepare_invoice_line_data(self, fiscal_position_id=None):
        self.ensure_one()
        account_id = self._get_account_id()
        taxes = self._get_tax_ids(fiscal_position_id)
        data = {
            "name": self._get_invoice_line_name(),
            "account_id": account_id.id if account_id else False,
            "price_unit": self.amount,
            "quantity": 1.0,
            "discount": 0.0,
            "product_uom_id": self.product_id and self.product_id.uom_id.id or False,
            "product_id": self.product_id and self.product_id.id or False,
            "tax_ids": taxes and [(6, 0, taxes.ids)] or [],
        }
        return data

    def action_view_invoice(self):
        invoices = self.mapped("move_id")
        action = self.env.ref("account.action_move_in_invoice_type").read()[0]
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action


class FleetVehicleCostInvoicingWizard(models.TransientModel):
    _name = "fleet.vehicle.cost.invoicing.wizard"

    def create_invoices(self):
        active_ids = self._context.get("active_ids", [])
        fleet_vehicle_log_services_ids = self.env["fleet.vehicle.log.services"].browse(
            active_ids
        )
        if fleet_vehicle_log_services_ids.state != "done":
            raise ValidationError(
                _("Only Done state services allow to create invoice.")
            )
        return self.create_invoice_from_costs(fleet_vehicle_log_services_ids)

    def _create_invoice(self, vendor, currency, company_id, costs):
        fiscal_position_id = False
        if vendor.property_account_position_id:
            fiscal_position_id = vendor.property_account_position_id
        invoice_line_ids = []
        for cost in costs:
            invoice_line_ids.append(
                (0, 0, cost._prepare_invoice_line_data(fiscal_position_id))
            )

        journal_domain = [("type", "=", "purchase"), ("company_id", "=", company_id.id)]
        if currency.id != company_id.currency_id.id:
            journal_domain.append(("currency_id", "=", currency.id))
        else:
            journal_domain.append(("currency_id", "=", False))

        journal_id = self.env["account.journal"].search(journal_domain, limit=1)
        if not journal_id:
            raise ValidationError(
                _("No Purchase Journal found for the currency %s") % (currency.name,)
            )

        invoice_obj = self.env["account.move"]
        invoice = invoice_obj.search(
            [
                ("partner_id", "=", vendor.id),
                ("state", "=", "draft"),
                ("move_type", "=", "in_invoice"),
                ("currency_id", "=", currency.id),
                ("company_id", "=", company_id.id),
                ("journal_id", "=", journal_id.id),
            ],
            limit=1,
        )

        if invoice:
            invoice.write({"invoice_line_ids": invoice_line_ids})
        else:
            invoice = invoice_obj.create(
                {
                    "move_type": "in_invoice",
                    "invoice_date": date.today(),
                    "partner_id": vendor.id,
                    "partner_shipping_id": vendor.id,
                    "invoice_line_ids": invoice_line_ids,
                    "currency_id": currency.id,
                    "fiscal_position_id": fiscal_position_id
                    and fiscal_position_id.id
                    or False,
                    "company_id": company_id.id,
                    "journal_id": journal_id.id,
                }
            )
        return invoice

    def create_invoice_from_costs(self, fleet_vehicle_cost_ids):
        if fleet_vehicle_cost_ids.move_id:
            raise ValidationError(_("This service has alerady been Invoiced"))
        data = {}

        for fleet in fleet_vehicle_cost_ids:
            if fleet.company_id not in data.keys():
                data[fleet.company_id] = {}

            if not fleet.currency_id:
                raise ValidationError(
                    _(
                        "The cost id: %d has no currency set. Hence, cannot create invoice for it."
                    )
                    % (fleet.id,)
                )
            if fleet.currency_id not in data[fleet.company_id].keys():
                data[fleet.company_id][fleet.currency_id] = {}

            if not fleet.vendor_id:
                raise ValidationError(
                    _(
                        "The cost id: %d has no vendor set. Hence, cannot create invoice for it."
                    )
                    % (fleet.id,)
                )

            if fleet.vendor_id not in data[fleet.company_id][fleet.currency_id].keys():
                data[fleet.company_id][fleet.currency_id][fleet.vendor_id] = []

            data[fleet.company_id][fleet.currency_id][fleet.vendor_id].append(fleet)

        for company_id in data.keys():
            for currency in data[company_id]:
                for vendor in data[company_id][currency]:
                    invoice = self._create_invoice(
                        vendor, currency, company_id, data[company_id][currency][vendor]
                    )
                    if invoice:
                        fleet_vehicle_cost_ids.move_id = invoice.id

        if self._context.get("open_invoices", False):
            return fleet_vehicle_cost_ids.action_view_invoice()
        return {"type": "ir.actions.act_window_close"}
