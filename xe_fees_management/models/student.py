import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class StudentProfile(models.Model):
    _inherit = "xe.student"

    is_academic = fields.Boolean(string="Is Academic Fees")
    is_activity = fields.Boolean()
    is_transport = fields.Boolean()
    is_boarding = fields.Boolean()
    is_optional = fields.Boolean()
    # old field
    fees_from_zone = fields.Many2one("xe.fees.type", string="From Zone", tracking=True)
    # new field
    fees_from_zone_id = fields.Many2one(
        "xe.fees.type", string="From Zone", tracking=True
    )
    # old field
    fees_to_zone = fields.Many2one("xe.fees.type", string="To Zone", tracking=True)
    # new field
    fees_to_zone_id = fields.Many2one("xe.fees.type", string="To Zone", tracking=True)
    fee_line_details_ids = fields.One2many(
        "xe.fees.line.details", "student_id", string="Transport Details"
    )
    transport_history_ids = fields.One2many("xe.transport.line.details", "student_id")
    activity_fee_ids = fields.Many2many("xe.fees.type")
    optional_fee_ids = fields.Many2many(
        "xe.fees.type", "xe_fees_type_optional", "fee_type_id", "optional_id"
    )
    is_transport_invoice = fields.Boolean()
    is_activity_invoice = fields.Boolean()
    is_boarding_invoice = fields.Boolean()
    is_optional_invoice = fields.Boolean()
    invoice_ids = fields.Many2many("account.move")

    @api.onchange("fees_to_zone_id")
    def _onchange_fee_based_student_update(self):
        if self.fees_to_zone_id:
            latest_fee = self.fees_to_zone_id
            inv_list = []
            fee_lines = self.env["xe.fees.details"].search(
                [("fee_type_id", "=", self.fees_to_zone_id.id)]
            )
            for fee in self.fee_line_details_ids:
                fee.sudo().unlink()
            for i in fee_lines:
                inv_list.append(
                    [
                        0,
                        0,
                        {
                            "fee_type_id": i.fee_type_id.id,
                            "term_id": i.term_id.id,
                            "invoice_date": i.invoice_date,
                            "due_date": i.due_date,
                            "schedule_date": i.schedule_date,
                            "amount": i.amount,
                            "student_id": self._origin.id,
                        },
                    ]
                )
            self.fee_line_details_ids = inv_list
            self.fees_to_zone_id = latest_fee
            self.fees_from_zone_id = self._origin.fees_to_zone_id
            account_move_rec = self.env["account.move"].search(
                [("partner_id", "=", self._origin.partner_id.id)]
            )
            self.write({"invoice_ids": [(6, 0, account_move_rec.ids)]})

    def update_invoice(self):
        inv_ids = []
        if self.is_transport:
            # Check Fee structure state as 'Draft' or not
            fee_details_rec = self.env["xe.fees.details"].search(
                [
                    ("fee_type_id", "=", self.fees_to_zone_id.id),
                    ("is_transport_fees", "=", self.is_transport),
                ],
                limit=1,
            )
            fee_struc_rec = fee_details_rec.fee_structure_id
            new_amount = fee_details_rec.amount
            if fee_struc_rec.state == "draft":
                raise UserError(
                    _(
                        "Invoice is not created for this Transport Fees Structure."
                        " Please Generate the invoice Fees."
                    )
                )
            # Check Fees From zone value is empty or not.
            # If it is empty, we don't proceed the invoice update logic.
            if self.fees_from_zone_id:
                amount_rec = self.env["account.move.line"].search(
                    [
                        (
                            "product_id",
                            "=",
                            self.fees_from_zone_id.product_id.product_variant_id.id,
                        ),
                        ("partner_id", "=", self.partner_id.id),
                        ("parent_state", "=", "draft"),
                    ]
                )
                amount_list = []
                for amt in amount_rec:
                    amount_list.append(amt.price_subtotal)

                # Tracking Logic
                inv_list = []
                amount_new_value = []
                val = 0
                amount_new_value.append(new_amount)
                inv_list.append(
                    [
                        0,
                        0,
                        {
                            "from_zone_id": self.fees_from_zone_id.id,
                            "to_zone_id": self.fees_to_zone_id.id,
                            "previous_amt": (
                                amount_list[val] if amount_list else new_amount
                            ),
                            "current_amt": new_amount,
                            "student_id": self.id,
                        },
                    ]
                )
                val = val + 1

                invoice_line_ids = []
                if self.invoice_ids:
                    for i in self.invoice_ids:
                        # Check Student Invoice state as 'Draft'
                        if i.state == "draft":
                            move_id = (
                                self.env["account.move"]
                                .sudo()
                                .search([("id", "=", i.id)], limit=1)
                            )
                            for inv_lin in i.invoice_line_ids:
                                fee_type = inv_lin.name
                                fee_type_trans_rec = (
                                    self.env["xe.fees.type"]
                                    .sudo()
                                    .search([("fee_type_id", "=", fee_type)])
                                )
                                if fee_type_trans_rec.type == "transport":
                                    val = 0
                                    move_line_id = inv_lin
                                    product = inv_lin.product_id
                                    account_id = inv_lin.account_id
                                    if move_line_id:
                                        self._cr.execute(
                                            """delete from account_move_line where id ="""
                                            + str(move_line_id.id)
                                        )
                                    move_line_vals = {
                                        "name": product.name,
                                        "account_id": account_id,
                                        "price_unit": (
                                            amount_new_value[val]
                                            if amount_new_value
                                            else new_amount
                                        ),
                                        "quantity": 1.0,
                                        "discount": 0.0,
                                        "product_id": product.id,
                                    }
                                    invoice_line_ids.append(([0, 0, move_line_vals]))
                                    move_id.write(
                                        {"invoice_line_ids": invoice_line_ids}
                                    )
                        # Check Invoice state as posted, we create a
                        # new invoice and updated to student profile.
                        if i.state == "posted":
                            invoice_date = i.invoice_date
                            invoice_payment_term_id = i.invoice_payment_term_id.id
                            invoice_date_due = i.invoice_date_due
                            for inv_lin in i.invoice_line_ids:
                                fee_type = inv_lin.name
                                fee_type_trans_rec = (
                                    self.env["xe.fees.type"]
                                    .sudo()
                                    .search([("fee_type_id", "=", fee_type)])
                                )
                                if fee_type_trans_rec.type == "transport":
                                    product = (
                                        self.fees_to_zone_id.product_id.product_variant_id
                                    )
                                    account_id = inv_lin.account_id
                                    price_total = new_amount
                                    move_line_vals = {
                                        "name": product.name,
                                        "account_id": account_id,
                                        "price_unit": price_total,
                                        "quantity": inv_lin.quantity,
                                        "discount": 0.0,
                                        "product_id": product.id,
                                    }
                                    invoice_line_ids.append(([0, 0, move_line_vals]))
                                else:
                                    product = inv_lin.product_id
                                    account_id = inv_lin.account_id
                                    price_total = inv_lin.price_total
                                    move_line_vals = {
                                        "name": product.name,
                                        "account_id": account_id,
                                        "price_unit": price_total,
                                        "quantity": inv_lin.quantity,
                                        "discount": 0.0,
                                        "product_id": product.id,
                                    }
                                    invoice_line_ids.append(([0, 0, move_line_vals]))

                            partner = i.partner_id
                            student = (
                                self.env["xe.student"]
                                .sudo()
                                .search([("name", "=", i.partner_id.name)], limit=1)
                            )
                            inv_type = "out_invoice"
                            reference = str(student.roll_number)
                            partner_id = partner.id
                            invoice_vals = {
                                "ref": reference,
                                "partner_id": partner_id,
                                "invoice_line_ids": invoice_line_ids,
                                "state": "draft",
                                "move_type": inv_type,
                                "invoice_payment_term_id": invoice_payment_term_id
                                or False,
                                "invoice_date": invoice_date or False,
                                "invoice_date_due": invoice_date_due or False,
                            }
                            self.env["account.move"].sudo().create(invoice_vals)

                # Update Transaction History
                self.transport_history_ids = inv_list
                account_move_rec = self.env["account.move"].search(
                    [("partner_id", "=", self.partner_id.id)]
                )
                self.write({"invoice_ids": [(6, 0, account_move_rec.ids)]})

        # Actitivty Logic
        if self.is_activity:
            struc_rec = self.env["xe.fees.structure"].search(
                [("is_activity", "=", self.is_activity)]
            )
            if struc_rec.invoice_id:
                raise ValidationError(_("Sorry, Invoice is already Generated."))
            if not struc_rec.invoice_ids:
                partner_id = self.partner_id
                student = self
                terms = struc_rec.fee_details_ids.mapped("term_id")
                invoice_dates = struc_rec.fee_details_ids.mapped("invoice_date")
                check_term = all(x == terms[0] for x in terms)
                check_date = all(x == invoice_dates[0] for x in invoice_dates)
                single_inv_act = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .search([("key", "=", "xe_fees_management.is_activity")], limit=1)
                )
                # Separate invoice should be generated based on the configuration activity field
                if not single_inv_act:
                    # Separate invoice should be generated based on the different Terms
                    if not check_term:
                        inv_line = (
                            self.env["xe.fees.details"]
                            .sudo()
                            .search(
                                [
                                    ("fee_type_id", "in", self.activity_fee_ids.ids),
                                    ("fee_structure_id", "=", struc_rec.id),
                                ]
                            )
                        )
                        for invoice_line in inv_line:
                            inv_ids = struc_rec.separate_invoice_create_fun(
                                invoice_line, student, partner_id
                            )

                    # Separate invoice should be generated based on the
                    # same Terms and different invoices dates
                    if check_term and not check_date:
                        inv_line = (
                            self.env["xe.fees.details"]
                            .sudo()
                            .search(
                                [
                                    ("invoice_date", "in", invoice_dates),
                                    ("fee_type_id", "in", self.activity_fee_ids.ids),
                                    ("fee_structure_id", "=", struc_rec.id),
                                ]
                            )
                        )
                        for invoice_line in inv_line:
                            inv_ids = struc_rec.separate_invoice_create_fun(
                                invoice_line, student, partner_id
                            )

                    # Single Invoice Generated based on same term and same invoice
                    if check_term and check_date:
                        inv_line = (
                            self.env["xe.fees.details"]
                            .sudo()
                            .search(
                                [
                                    ("invoice_date", "in", invoice_dates),
                                    ("fee_type_id", "in", self.activity_fee_ids.ids),
                                    ("fee_structure_id", "=", struc_rec.id),
                                ]
                            )
                        )
                        inv_ids = struc_rec.separate_invoice_create_fun(
                            inv_line, student, partner_id
                        )

                # Single Invoice Generated based on same term and same invoice date for all line
                if single_inv_act:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("fee_type_id", "in", self.activity_fee_ids.ids),
                                ("fee_structure_id", "=", struc_rec.id),
                            ]
                        )
                    )
                    inv_ids = struc_rec.with_context(
                        inv_line=inv_line, single_inv_act=single_inv_act
                    ).single_invoice_create_fun(student, partner_id, terms)

                # Invoice ID map with fees structure
                if inv_ids:
                    account_move_rec = self.env["account.move"].search(
                        [("id", "=", inv_ids)]
                    )
                    self.write({"invoice_ids": [(6, 0, account_move_rec.ids)]})

        # Optional Fee
        if self.is_optional:
            struc_rec = self.env["xe.fees.structure"].search(
                [("is_optional", "=", self.is_optional)]
            )
            if struc_rec.invoice_id:
                raise ValidationError(_("Sorry, Invoice is already Generated."))
            if not struc_rec.invoice_ids:
                partner_id = self.partner_id
                student = self
                terms = struc_rec.fee_details_ids.mapped("term_id")
                invoice_dates = struc_rec.fee_details_ids.mapped("invoice_date")
                check_term = all(x == terms[0] for x in terms)
                check_date = all(x == invoice_dates[0] for x in invoice_dates)
                single_inv_act = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .search([("key", "=", "xe_fees_management.is_optional")], limit=1)
                )

                # Separate invoice should be generated based on the configuration activity field
                if not single_inv_act:
                    # Separate invoice should be generated based on the different Terms
                    if not check_term:
                        inv_line = (
                            self.env["xe.fees.details"]
                            .sudo()
                            .search(
                                [
                                    ("fee_type_id", "in", self.optional_fee_ids.ids),
                                    ("fee_structure_id", "=", struc_rec.id),
                                ]
                            )
                        )
                        for invoice_line in inv_line:
                            inv_ids = struc_rec.separate_invoice_create_fun(
                                invoice_line, student, partner_id
                            )

                    # Separate invoice should be generated based on the
                    # same Terms and different invoices dates
                    if check_term and not check_date:
                        inv_line = (
                            self.env["xe.fees.details"]
                            .sudo()
                            .search(
                                [
                                    ("invoice_date", "in", invoice_dates),
                                    ("fee_type_id", "in", self.optional_fee_ids.ids),
                                    ("fee_structure_id", "=", struc_rec.id),
                                ]
                            )
                        )
                        for invoice_line in inv_line:
                            inv_ids = struc_rec.separate_invoice_create_fun(
                                invoice_line, student, partner_id
                            )

                    # Single Invoice Generated based on same term and same invoice
                    if check_term and check_date:
                        inv_line = (
                            self.env["xe.fees.details"]
                            .sudo()
                            .search(
                                [
                                    ("invoice_date", "in", invoice_dates),
                                    ("fee_type_id", "in", self.optional_fee_ids.ids),
                                    ("fee_structure_id", "=", struc_rec.id),
                                ]
                            )
                        )
                        inv_ids = struc_rec.separate_invoice_create_fun(
                            inv_line, student, partner_id
                        )

                # Single Invoice Generated based on same term and same invoice date for all line
                if single_inv_act:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("fee_type_id", "in", self.optional_fee_ids.ids),
                                ("fee_structure_id", "=", struc_rec.id),
                            ]
                        )
                    )
                    inv_ids = struc_rec.with_context(
                        inv_line=inv_line, single_inv_act=single_inv_act
                    ).single_invoice_create_fun(student, partner_id, terms)

                # Invoice ID map with fees structure
                if inv_ids:
                    account_move_rec = self.env["account.move"].search(
                        [("id", "=", inv_ids)]
                    )
                    self.write({"invoice_ids": [(6, 0, account_move_rec.ids)]})

    def write(self, vals):
        if vals.get("fees_to_zone_id"):
            latest_fee = vals.get("fees_to_zone_id")
            inv_list = []
            for fee in self.fee_line_details_ids:
                fee.sudo().unlink()
            fee_lines = self.env["xe.fees.details"].search(
                [("fee_type_id", "=", latest_fee)]
            )
            for i in fee_lines:
                inv_list.append(
                    [
                        0,
                        0,
                        {
                            "fee_type_id": i.fee_type_id.id,
                            "term_id": i.term_id.id,
                            "invoice_date": i.invoice_date,
                            "due_date": i.due_date,
                            "schedule_date": i.schedule_date,
                            "amount": i.amount,
                            "student_id": self.id,
                        },
                    ]
                )
            vals["fee_line_details_ids"] = inv_list
            vals["fees_from_zone_id"] = self._origin.fees_to_zone_id
            account_move_rec = self.env["account.move"].search(
                [("partner_id", "=", self._origin.partner_id.id)]
            )
            vals["invoice_ids"] = [(6, 0, account_move_rec.ids)]
        result = super(StudentProfile, self).write(vals)
        # self.clear_caches()
        return result

    @api.model
    def create(self, vals):
        result = super(StudentProfile, self).create(vals)
        if vals.get("fees_to_zone_id"):
            latest_fee = vals.get("fees_to_zone_id")
            inv_list = []
            for fee in result.fee_line_details_ids:
                fee.sudo().unlink()
            fee_lines = self.env["xe.fees.details"].search(
                [("fee_type_id", "=", latest_fee)]
            )
            for i in fee_lines:
                inv_list.append(
                    [
                        0,
                        0,
                        {
                            "fee_type_id": i.fee_type_id.id,
                            "term": i.term.id,
                            "invoice_date": i.invoice_date,
                            "due_date": i.due_date,
                            "schedule_date": i.schedule_date,
                            "amount": i.amount,
                            "student_id": result.id,
                        },
                    ]
                )
            result.fee_line_details_ids = inv_list
            result.fees_from_zone_id = result._origin.fees_to_zone_id
            account_move_rec = self.env["account.move"].search(
                [("partner_id", "=", self._origin.partner_id.id)]
            )
            result.invoice_ids = [(6, 0, account_move_rec.ids)]
        self.clear_caches()
        return result


class XeStudentFeesDetails(models.Model):
    _name = "xe.student.fees.details"
    _description = "Student Fees Details"

    @api.depends("fee_sub_line_ids")
    def _compute_get_amount2(self):
        for line in self:
            if line.fee_sub_line_ids:
                line.amount2 = sum(
                    line.fee_sub_line_ids.filtered(lambda d: d.is_invoice)
                    .mapped("fee_term_line_id")
                    .mapped("value")
                )
            else:
                line.amount2 = 0

    def get_invoice_vals(self, student, partner_id, invoice_line_ids):
        move_type = "out_invoice"
        reference = (student.roll_number or False,)
        result = {
            "move_type": move_type,
            "ref": reference,
            "partner_id": partner_id.id,
            "invoice_line_ids": invoice_line_ids,
            "state": "draft",
        }
        return result

    fees_term_line_ids = fields.Many2many("xe.fees.term.line", string="Fees Term Lines")
    product_ids = fields.Many2many("product.product", string="Products")
    invoice_id = fields.Many2one("account.move")
    amount = fields.Float("Fees Amount")
    date = fields.Date("Invoice Date")
    student_id = fields.Many2one("xe.student")
    state = fields.Selection(
        [("draft", "Draft"), ("invoice", "Invoice Created")], "Status"
    )
    invoice_state = fields.Selection(related="invoice_id.state", readonly=True)
    fee_sub_line_ids = fields.One2many(
        "xe.fee.sub.lines", "fee_line_id", string="Fees Sub Lines"
    )
    amount2 = fields.Float("Invoice Amount", compute="_compute_get_amount2")

    def view_invoice(self):
        value = True
        if self.invoice_id:
            form_view = self.env.ref("account.view_move_form")
            tree_view = self.env.ref("account.view_out_invoice_tree")
            value = {
                "domain": str([("id", "=", self.invoice_id.id)]),
                "view_type": "form",
                "view_mode": "form",
                "res_model": "account.move",
                "view_id": False,
                "views": [
                    (form_view and form_view.id or False, "form"),
                    (tree_view and tree_view.id or False, "tree"),
                ],
                "type": "ir.actions.act_window",
                "res_id": self.invoice_id.id,
                "target": "current",
                "nodestroy": True,
            }
        return value

    def create_invoice(self):
        inv_obj = self.env["account.move"]
        partner_id = self.student_id.partner_id
        student = self.student_id
        invoice_line_ids = []
        fee_sub_line_ids = self.fee_sub_line_ids
        for line in fee_sub_line_ids:
            if line.is_invoice:
                rec = line.fee_term_line_id
            else:
                continue
            account_id = False
            product = rec.product_id
            if product.property_account_income_id:
                account_id = product.property_account_income_id.id
            if not account_id:
                account_id = product.categ_id.property_account_income_categ_id.id
            if not account_id:
                raise UserError(
                    _('There is no income account defined for this product: "%s"')
                    % rec.product_id.name
                )
            inv_line_vals = {
                "name": product.name,
                "account_id": account_id,
                "price_unit": rec.value,
                "quantity": 1.0,
                "discount": 0.0,
                "product_id": product.id,
            }
            invoice_line_ids.append([0, 0, inv_line_vals])
        invoice_vals = self.get_invoice_vals(student, partner_id, invoice_line_ids)
        invoice = inv_obj.create(invoice_vals)
        self.write({"state": "invoice", "invoice_id": invoice.id})
        return True

    def get_invoice_vals_for_crone(self, line, invoice_line_vals):
        move_type = "out_invoice"
        reference = line.student_id.roll_number
        partner_id = line.student_id.partner_id.id
        invoice_line_ids = invoice_line_vals
        result = {
            "move_type": move_type,
            "ref": reference,
            "partner_id": partner_id,
            "invoice_line_ids": invoice_line_ids,
        }
        return result

    @api.model
    def get_invoice_crone(self, validate_with_in=0, validate_type=""):
        """Create invoice for fee payment process of student"""
        inv_obj = self.env["account.move"]
        student_objs = self.env["xe.student"].search(
            [("active", "=", True), ("alumni_boolean", "=", False)]
        )
        student_ids = student_objs.mapped("id")
        fee_lines_with_no_invoice = self.env["xe.student.fees.details"].search(
            [("invoice_id", "=", False), ("student_id", "in", student_ids)]
        )
        for line in fee_lines_with_no_invoice:
            due_date = fields.Date.from_string(line.date) + relativedelta(days=15)
            gr_no = line.student_id.gr_no
            user_id = self.env.context.get("uid")
            company_id = self.env["res.users"].browse(user_id).company_id.id
            xenesis_base = self.env["ir.module.module"].search(
                [("name", "=", "xenesis_school_base"), ("state", "=", "installed")]
            )
            if xenesis_base:
                company_id = (
                    line.student_id
                    and line.student_id.company_id
                    and line.student_id.company_id.id
                )

            date = line.date
            x_date = line.date
            if validate_type == "before" and validate_with_in > 0:
                x_date = str(
                    fields.Date.from_string(line.date)
                    - relativedelta(days=validate_with_in)
                )
            elif validate_type == "after" and validate_with_in > 0:
                x_date = str(
                    fields.Date.from_string(line.date)
                    + relativedelta(days=validate_with_in)
                )
            elif validate_with_in < 0 or not validate_type:
                raise UserError(
                    _(
                        "Put Positive number in Validate within field inside the schedule action: "
                        "Create and Validate invoice for Fee collection or Define validate type"
                    )
                )
            fee_line_ids = self.env["xe.student.fee.lines"].search(
                [("student_fee_detail_id", "=", line.id), ("is_invoice", "!=", False)]
            )
            invoice_line_vals = []
            for fee in fee_line_ids:
                account_id = (
                    fee.fee_term_line_id.product_id.property_account_income_id.id
                    or fee.fee_term_line_id.product_id.categ_id.property_account_income_categ_id.id
                )
                account_id = self.find_income_account_id(
                    fee.fee_term_line_id.product_id, company_id
                )

                price_unit = fee.fee_term_line_id.value
                if fee.fee_term_line_id.fees_id.transport_fees:
                    if fee.fee_term_line_id.start_date == date:
                        price_unit = fee.fee_term_line_id.value
                    if fee.fee_term_line_id.term2_start_date == date:
                        price_unit = fee.fee_term_line_id.term2_value
                    if fee.fee_term_line_id.term3_start_date == date:
                        price_unit = fee.fee_term_line_id.term3_value

                vals_dict = {
                    "name": fee.fee_term_line_id.product_id.name,
                    "origin": gr_no,
                    "date_invoice": date,
                    "date_due": due_date,
                    "account_id": account_id,
                    "price_unit": price_unit,
                    "quantity": 1.0,
                    "discount": 0.0,
                    "uom_id": fee.fee_term_line_id.product_id.uom_id.id,
                    "product_id": fee.fee_term_line_id.product_id.id,
                    "company_id": company_id,
                }
                invoice_line_vals.append([0, 0, vals_dict])
                admission_fee_dict = self.get_admission_fee_dict(
                    line.student_id, self.date, due_date
                )
                if admission_fee_dict:
                    invoice_line_vals.append([0, 0, admission_fee_dict])
            current_date = str(datetime.now())[:10]
            if current_date >= x_date:
                invoice_vals = self.get_invoice_vals_for_crone(line, invoice_line_vals)
                invoice = inv_obj.create(invoice_vals)
                invoice.compute_taxes()
                line.write({"state": "invoice", "invoice_id": invoice.id})
                invoice.write({"date_due": due_date})

    def get_invoice(self):
        """Create invoice for fee payment process of student"""
        user_id = self.env.context.get("uid")
        company_id = self.env["res.users"].browse(user_id).company_id.id
        inv_obj = self.env["account.move"]
        partner_id = self.student_id.partner_id
        date = self.date
        student = self.student_id
        alumni = student.alumni_boolean
        if alumni:
            raise UserError(_("you cannot create invoice for Alumni"))

        student_company_id = company_id
        xenesis_base = self.env["ir.module.module"].search(
            [("name", "=", "xenesis_school_base"), ("state", "=", "installed")]
        )
        if xenesis_base:
            student_company_id = (
                student and student.company_id and student.company_id.id
            )
        if student.company_id.id == company_id:
            invoice_line_ids = []
            due_date = fields.Date.from_string(self.date) + relativedelta(days=15)
            fee_line_ids = self.fee_line_ids
            for line in fee_line_ids:
                if line.is_invoice:
                    rec = line.fee_term_line_id
                else:
                    continue
                product = rec.product_id
                account_id = self.find_income_account_id(product, student_company_id)

                if not account_id:
                    raise UserError(
                        _(
                            f"There is no income account defined for this product: {rec.product_id.name}."
                            f"You may have to install a chart of account from Accounting app, settings menu."
                        )
                    )
                if rec.value <= 0.00:
                    raise UserError(
                        _("The value of the deposit amount must be positive.")
                    )

                price_unit = rec.value
                if rec.fees_id.transport_fees:
                    if rec.start_date == date:
                        price_unit = rec.value
                    if rec.term2_start_date == date:
                        price_unit = rec.term2_value
                    if rec.term3_start_date == date:
                        price_unit = rec.term3_value

                inv_line_vals = {
                    "name": product.name,
                    "origin": student.gr_no,
                    "date_invoice": self.date,
                    "date_due": due_date,
                    "account_id": account_id,
                    "price_unit": price_unit,
                    "quantity": 1.0,
                    "discount": 0.0,
                    "uom_id": product.uom_id.id,
                    "product_id": product.id,
                    "company_id": student_company_id,
                }
                invoice_line_ids.append([0, 0, inv_line_vals])

                admission_fee_dict = self.get_admission_fee_dict(
                    student, self.date, due_date
                )
                if admission_fee_dict:
                    invoice_line_ids.append([0, 0, admission_fee_dict])

            invoice_vals = self.get_invoice_vals_for_button(
                student, partner_id, invoice_line_ids
            )
            invoice = inv_obj.create(invoice_vals)
            invoice.compute_taxes()
            self.write({"state": "invoice", "invoice_id": invoice.id})
            invoice.write({"date_due": due_date})
        return True


class StudentFeeSubLine(models.Model):
    _name = "xe.fee.sub.lines"
    _description = "Student Fees Sub Line"

    is_invoice = fields.Boolean(default=True, string="Add to Invoice")
    fee_term_line_id = fields.Many2one("xe.fees.term.line", string="Fee Term Line")
    fee_line_id = fields.Many2one("xe.student.fees.details", string="Fee Line ID")
    state = fields.Selection(related="fee_line_id.state")
