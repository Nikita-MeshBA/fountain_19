import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class FeesTerm(models.Model):
    _name = "xe.fees.term"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fees Term Form"

    @api.model
    def create(self, vals):
        result = super(FeesTerm, self).create(vals)
        course = result.course_id
        course.sudo().write({"fees_term_id": result.id})

        if not result.route_line and not result.fees_line:
            raise UserError(_("Fees Terms must be Required!"))
        return result

    def write(self, values):
        if "course_id" in values:
            course_obj = self.env["xe.course"].browse(values["course_id"])
            course_obj.sudo().write({"fees_term_id": self.id})
        result = super(FeesTerm, self).write(values)
        return result

    @api.onchange("transport_fees")
    def onchange_transport_fees(self):
        if self.transport_fees:
            self.course_id = False

    note = fields.Text("Description")
    course_id = fields.Many2one("xe.course", string="Class")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    no_days = fields.Integer("No of Days")
    day_type = fields.Selection([("before", "Before"), ("after", "After")], "Type")
    fees_line = fields.One2many("xe.fees.term.line", "fees_term_id", "Terms")
    route_line = fields.One2many("xe.fees.term.line", "fees_term_id", "Terms")
    name = fields.Char("Fees Terms", required=True)
    transport_fees = fields.Boolean()


class FeesTermLine(models.Model):
    _name = "xe.fees.term.line"
    _description = "Fees Term Line"
    _rec_name = "product_id"

    fees_term_id = fields.Many2one("xe.fees.term", "Fees")
    description = fields.Char()
    product_id = fields.Many2one("product.product", "Product")
    route = fields.Char()
    fee_type = fields.Selection([("term", "Term"), ("year", "Year")])
    start_date = fields.Date()
    end_date = fields.Date()
    value = fields.Float()
    company_id = fields.Many2one(
        "res.company", "Company", related="fees_term_id.company_id"
    )


class FeesDetails(models.Model):
    _name = "xe.fees.details"
    _description = "Fees details"
    _rec_name = "fee_type_id"

    fee_structure_id = fields.Many2one(
        "xe.fees.structure", string="Fee Structure Line", ondelete="cascade"
    )
    is_academic = fields.Boolean(
        related="fee_structure_id.is_academic", string="Is Academic Fees"
    )
    is_activity = fields.Boolean(
        related="fee_structure_id.is_activity", string="Is Activity Fees"
    )
    is_transport_fees = fields.Boolean(
        related="fee_structure_id.is_transport_fees", string="Is Transport Fees"
    )
    is_boarding = fields.Boolean(
        related="fee_structure_id.is_boarding", string="Is Boarding Fees"
    )
    is_optional = fields.Boolean(
        related="fee_structure_id.is_optional", string="Is Optional Fees"
    )
    # old field
    fee_type = fields.Many2one("xe.fees.type")
    # new field
    # fee_type_id = fields.Many2one("xe.fees.type", required=True)
    fee_type_id = fields.Many2one("xe.fees.type")
    # old field
    academic_year = fields.Many2one("xe.academic.year")
    # new field
    academic_year_id = fields.Many2one("xe.academic.year")
    term_id = fields.Many2one(
        "xe.academic.terms", string="Terms", related="fee_structure_id.term_id"
    )
    due_days = fields.Integer(related="fee_structure_id.due_days", store=True)
    invoice_date = fields.Date(related="fee_structure_id.invoice_date")
    due_date = fields.Date(compute="_compute_due_date", store=True)
    schedule_date = fields.Date()
    currency_id = fields.Many2one("res.currency")
    # old field
    receipt_name = fields.Many2one("fee.receipt")
    # new field
    receipt_name_id = fields.Many2one("fee.receipt")
    amount = fields.Monetary(currency_field="currency_id")
    student_id = fields.Many2one("xe.student", string="Student ID")
    parent_state = fields.Selection(
        [("draft", "Draft"), ("invoice", "Invoice Created")],
        default="draft",
        string="Status",
        tracking=True,
    )
    company_id = fields.Many2one("res.company", related="fee_structure_id.company_id")

    @api.depends("due_days")
    def _compute_due_date(self):
        for i in self:
            current_date = datetime.datetime.now().date()
            self.due_date = current_date + datetime.timedelta(days=int(i.due_days))

    @api.onchange("fee_type_id")
    def _onchange_fees_type(self):
        if self.fee_type_id:
            self.amount = self.fee_type_id.product_id.list_price


class FeesLineDetails(models.Model):
    _name = "xe.fees.line.details"
    _description = "Fees Line details"
    _rec_name = "fee_type_id"

    fee_structure_id = fields.Many2one(
        "xe.fees.structure", string="Fee Structure Line", ondelete="cascade"
    )
    is_transport_fees = fields.Boolean(related="fee_structure_id.is_transport_fees")
    # old field
    fee_type = fields.Many2one("xe.fees.type")
    # new field
    # fee_type_id = fields.Many2one("xe.fees.type", required=True)
    fee_type_id = fields.Many2one("xe.fees.type")
    # old field
    academic_year = fields.Many2one("xe.academic.year")
    # new field
    academic_year_id = fields.Many2one("xe.academic.year")
    # old field
    term = fields.Many2one("xe.academic.terms", string="Terms")
    # new field
    term_id = fields.Many2one("xe.academic.terms", string="Terms")
    due_days = fields.Integer(related="fee_structure_id.due_days", store=True)
    due_date = fields.Date()
    invoice_date = fields.Date()
    schedule_date = fields.Date()
    currency_id = fields.Many2one("res.currency")
    # old field
    receipt_name = fields.Many2one("fee.receipt")
    # new field
    receipt_name_id = fields.Many2one("fee.receipt")
    amount = fields.Monetary(currency_field="currency_id")
    student_id = fields.Many2one("xe.student", string="Student ID")
    company_id = fields.Many2one("res.company", related="fee_structure_id.company_id")


class TransportDetails(models.Model):
    _name = "xe.transport.line.details"
    _description = "Transport Line details"
    _rec_name = "to_zone_id"

    fee_structure_id = fields.Many2one("xe.fees.structure", string="Fee Structure Line")
    # old field
    from_zone = fields.Many2one("xe.fees.type", tracking=True)
    # new field
    from_zone_id = fields.Many2one("xe.fees.type", tracking=True)
    # old field
    to_zone = fields.Many2one("xe.fees.type", tracking=True)
    # new field
    to_zone_id = fields.Many2one("xe.fees.type", tracking=True)
    currency_id = fields.Many2one("res.currency")
    previous_amt = fields.Monetary(currency_field="currency_id")
    current_amt = fields.Monetary(currency_field="currency_id")
    invoice_line_id = fields.Integer()
    student_id = fields.Many2one("xe.student", string="Student ID")
    company_id = fields.Many2one("res.company", related="fee_structure_id.company_id")
