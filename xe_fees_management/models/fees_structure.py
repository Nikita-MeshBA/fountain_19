from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, _


class FeesStructure(models.Model):
    _name = "xe.fees.structure"
    _inherit = ["mail.thread"]
    _description = "Fees Structure"
    _rec_name = "name"

    # old field
    academic_year = fields.Many2one("xe.academic.year", tracking=True)
    # new field
    academic_year_id = fields.Many2one("xe.academic.year", tracking=True)
    name = fields.Char(tracking=True)
    code = fields.Char()
    course_id = fields.Many2many("xe.course", string="Class", tracking=True)
    classroom_id = fields.Many2many("xe.classroom", string="Class Room", tracking=True)
    fee_details_ids = fields.One2many(
        "xe.fees.details", "fee_structure_id", string="Fees Details", tracking=True
    )
    # old field
    payment_term = fields.Many2one("account.payment.term", tracking=True)
    # new field
    payment_term_id = fields.Many2one("account.payment.term", tracking=True)
    due_days = fields.Integer()
    currency_id = fields.Many2one("res.currency")
    invoice_id = fields.Many2one("account.move")
    invoice_ids = fields.Many2many("account.move")
    is_transport_fees = fields.Boolean(default=False)
    is_academic = fields.Boolean(string="Is Academic Fees", default=True)
    is_activity = fields.Boolean(string="Is Activity Fees")
    is_boarding = fields.Boolean(string="Is Boarding Fees")
    is_optional = fields.Boolean(string="Is Optional Fees")
    student_ids = fields.Many2many("xe.student")
    fee_structu_type = fields.Selection(
        [
            ("academic", "Academic Fees"),
            # ("transport", "Transport Fees"),
            # ("activity", "Activity Fees"),
            # ("boarding", "Boarding Fees"),
            # ("optional", "Optional Fees"),
        ],
        default="academic",
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    is_include_transport_fees = fields.Boolean(string="Include Transport")
    is_include_optional_fees = fields.Boolean(string="Include Optional Fees")
    is_include_activity_fees = fields.Boolean(string="Include Activity Fees.")
    # old field
    term = fields.Many2one("xe.academic.terms")
    # new field
    term_id = fields.Many2one("xe.academic.terms")
    invoice_date = fields.Date()

    @api.onchange("is_include_transport_fees")
    def _onchange_is_include_transport_fees(self):
        if self.is_include_transport_fees:
            self.is_transport_fees = True
        else:
            self.is_transport_fees = False

    @api.onchange("is_include_optional_fees")
    def _onchange_is_include_optional_fees(self):
        if self.is_include_optional_fees:
            self.is_optional = True
        else:
            self.is_optional = False

    @api.onchange("is_include_activity_fees")
    def _onchange_is_include_activity_fees(self):
        if self.is_include_activity_fees:
            self.is_activity = True
        else:
            self.is_activity = False

    # @api.onchange("course_id", "fee_structu_type")
    @api.onchange("course_id")
    def _onchange_course_ids(self):
        if self.course_id:
            class_room_rec = (
                self.env["xe.classroom"]
                .sudo()
                .search([("course_id", "in", self.course_id.ids)])
            )
            self.write({"classroom_id": [(6, 0, class_room_rec.ids)]})
        else:
            self.write({"classroom_id": [(6, 0, [])]})

        # if self.fee_structu_type == "transport":
        #     self.is_transport_fees = True
        #     self.is_academic = (
        #         self.is_boarding
        #     ) = self.is_activity = self.is_optional = False
        # elif self.fee_structu_type == "academic":
        #     self.is_academic = True
        #     self.is_transport_fees = (
        #         self.is_activity
        #     ) = self.is_boarding = self.is_optional = False
        # elif self.fee_structu_type == "activity":
        #     self.is_activity = True
        #     self.is_academic = (
        #         self.is_boarding
        #     ) = self.is_transport_fees = self.is_optional = False
        # elif self.fee_structu_type == "boarding":
        #     self.is_boarding = True
        #     self.is_academic = (
        #         self.is_activity
        #     ) = self.is_transport_fees = self.is_optional = False
        # elif self.fee_structu_type == "optional":
        #     self.is_optional = True
        #     self.is_academic = (
        #         self.is_activity
        #     ) = self.is_transport_fees = self.is_boarding = False
        # else:
        #     self.is_academic = (
        #         self.is_transport_fees
        #     ) = self.is_activity = self.is_boarding = self.is_optional = False

    # @api.depends("fee_details_ids")
    # def _get_amount2(self):
    #     for line in self:
    #         if line.fee_details_ids:
    #             line.amount2 = sum(line.fee_sub_line_ids.mapped("amount"))
    #         else:
    #             line.amount2 = 0

    @api.onchange("payment_term_id")
    def _onchange_payment_term(self):
        if self.payment_term_id:
            due_days = self.payment_term_id.line_ids.mapped("nb_days")[0]
            self.due_days = due_days

    def get_invoice_vals(self, student, partner_id, invoice_line_ids):
        partner = partner_id
        inv_type = "out_invoice"
        reference = str(student.roll_number)
        partner_id = partner.id
        result = {
            "ref": reference,
            "partner_id": partner_id,
            "invoice_line_ids": invoice_line_ids,
            "state": "draft",
            "move_type": inv_type,
            "invoice_payment_term_id": self.payment_term_id.id,
        }
        return result

    def create_invoice_line_values(self, account, product, line):
        return {
            "name": line.receipt_name_id.name or product.name,
            "receipt_name_id": line.receipt_name_id.id,
            "account_id": account,
            "price_unit": line.amount,
            "quantity": 1.0,
            "discount": 0.0,
            "product_id": product.id,
        }

    # Invoice Generation Odoo
    def generate_fees_lines1(self):
        current_date = fields.date.today()
        fees_details_rec = (
            self.env["xe.fees.details"]
            .sudo()
            .search([("schedule_date", "=", current_date)])
        )
        fees_ids = [i.fee_structure_id.id for i in fees_details_rec]
        fees_struc_rec = (
            self.env["xe.fees.structure"]
            .sudo()
            .search([("id", "in", list(set(fees_ids)))])
        )
        for fee in fees_struc_rec:
            inv_obj = self.env["account.move"]
            course = fee.course_id.ids
            classroom = fee.classroom_id.ids
            student_rec = self.env["xe.student"].search(
                [
                    ("course_id", "in", course),
                    ("classroom_id", "in", classroom),
                    ("current_academic_year_id", "=", fee.academic_year_id.id),
                ]
            )
            inv_ids = []
            for i in student_rec:
                partner_id = i.partner_id
                student = i
                invoice_line_ids = []
                terms = fee.fee_details_ids.mapped("term_id")
                invoice_dates = fee.fee_details_ids.mapped("invoice_date")
                check_term = all(x == terms[0] for x in terms)
                check_date = all(x == invoice_dates[0] for x in invoice_dates)
                # Separate invoice should be generated based on the different Terms
                if not check_term:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", fee.id),
                                ("parent_state", "=", "draft"),
                            ]
                        )
                    )
                    for line in inv_line:
                        invoice_date = line.invoice_date
                        term = line.term_id.name
                        account_id = False
                        product_temp = (
                            self.env["product.template"]
                            .sudo()
                            .search(
                                [("id", "=", line.fee_type_id.product_id.id)], limit=1
                            )
                        )
                        product = product_temp.product_variant_id
                        if product.property_account_income_id:
                            account_id = product.property_account_income_id.id
                        if not account_id:
                            account_id = (
                                product.categ_id.property_account_income_categ_id.id
                            )
                        if not account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s"'
                                )
                                % product.name
                            )

                        inv_line_vals = self.create_invoice_line_values(
                            account_id, product, line
                        )
                        invoice_line_ids.append([0, 0, inv_line_vals])
                        invoice_vals = fee.get_invoice_vals(
                            student, partner_id, invoice_line_ids
                        )
                        invoice = inv_obj.create(invoice_vals)
                        invoice.invoice_date = invoice_date
                        invoice.terms = str(term)
                        fee.invoice_id = invoice.id
                        invoice_line_ids.clear()
                        inv_ids.append(invoice.id)
                # Separate invoice should be generated based on the different invoice Dates
                if check_term and check_date == False:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", fee.id),
                                ("parent_state", "=", "draft"),
                            ]
                        )
                    )
                    for line in inv_line:
                        invoice_date = line.invoice_date
                        term = line.term_id.name
                        account_id = False
                        product_temp = (
                            self.env["product.template"]
                            .sudo()
                            .search(
                                [("id", "=", line.fee_type_id.product_id.id)], limit=1
                            )
                        )
                        product = product_temp.product_variant_id
                        if product.property_account_income_id:
                            account_id = product.property_account_income_id.id
                        if not account_id:
                            account_id = (
                                product.categ_id.property_account_income_categ_id.id
                            )
                        if not account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s"'
                                )
                                % product.name
                            )

                        inv_line_vals = self.create_invoice_line_values(
                            account_id, product, line
                        )
                        invoice_line_ids.append([0, 0, inv_line_vals])
                        invoice_vals = fee.get_invoice_vals(
                            student, partner_id, invoice_line_ids
                        )
                        invoice = inv_obj.create(invoice_vals)
                        invoice.invoice_date = invoice_date
                        invoice.terms = str(term)
                        fee.invoice_id = invoice.id
                        invoice_line_ids.clear()
                        inv_ids.append(invoice.id)
                # Single Invoice Generated based on same term and same invoice date for all line
                if check_term and check_date:
                    for line in fee.fee_details_ids:
                        invoice_date = line.invoice_date
                        account_id = False
                        product_temp = (
                            self.env["product.template"]
                            .sudo()
                            .search(
                                [("id", "=", line.fee_type_id.product_id.id)], limit=1
                            )
                        )
                        product = product_temp.product_variant_id
                        if product.property_account_income_id:
                            account_id = product.property_account_income_id.id
                        if not account_id:
                            account_id = (
                                product.categ_id.property_account_income_categ_id.id
                            )
                        if not account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s"'
                                )
                                % product.name
                            )
                        inv_line_vals = self.create_invoice_line_values(
                            account_id, product, line
                        )
                        invoice_line_ids.append([0, 0, inv_line_vals])
                    invoice_vals = fee.get_invoice_vals(
                        student, partner_id, invoice_line_ids
                    )
                    invoice = inv_obj.create(invoice_vals)
                    invoice.invoice_date = invoice_date
                    invoice.terms = str(terms.name)
                    fee.invoice_id = invoice.id
                    inv_ids.append(invoice.id)

                # Invoice ID map with fees structure
                account_invoices = (
                    self.env["account.move"].sudo().search([("id", "in", inv_ids)])
                )
                fee.write({"invoice_ids": [(6, 0, account_invoices.ids)], "terms": ""})

    # Generate Button Login transport added
    def generate_transport(self):
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        # single_inv = (
        #     self.env["ir.config_parameter"]
        #     .sudo()
        #     .search([("key", "=", "xe_fees_management.is_transport")], limit=1)
        # )
        single_inv = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_fees_management.is_transport")
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            current_academic_year_id = academic_rec.id
        else:
            current_academic_year_id = self.academic_year_id.id
        # Fetch the student record based on current academic year
        student_rec = self.env.context.get("student_rec")
        term = self.env.context.get("term_id")
        course = self.course_id.ids
        classroom = self.classroom_id.ids
        student_domain = [("current_academic_year_id", "=", current_academic_year_id)]
        if course:
            student_domain.append(("course_id", "in", course))
        if classroom:
            student_domain.append(("classroom_id", "in", classroom))
        if not student_rec:
            student_domain.append(("is_transport", "=", True))
            student_rec = self.env["xe.student"].search(student_domain)

        inv_ids = []
        if self.is_include_transport_fees:
            for i in student_rec:
                partner_id = i.partner_id
                student = i
                inv_line = self.env["xe.fees.details"].create(
                    {
                        "invoice_date": self.invoice_date,
                        "fee_type_id": student.fees_to_zone_id.id,
                        "fee_type": student.fees_to_zone_id.id,
                        "term_id": self.term_id.id,
                        "parent_state": "draft",
                        "amount": student.fees_to_zone_id.product_id.list_price,
                    }
                )
                terms = self.fee_details_ids.mapped("term_id")
                invoice_dates = self.fee_details_ids.mapped("invoice_date")
                check_term = all(x == terms[0] for x in terms)
                check_date = all(x == invoice_dates[0] for x in invoice_dates)

                if not single_inv:
                    # Separate invoice should be generated based on the different Terms
                    if check_term == False:
                        for i in terms:
                            # inv_line = (
                            #     self.env["xe.fees.details"]
                            #     .sudo()
                            #     .search(
                            #         [
                            #             ("term", "=", term),
                            #             ("fee_structure_id", "=", self.id),
                            #             ("parent_state", "=", "draft"),
                            #         ]
                            #     )
                            # )
                            inv_id = self.separate_invoice_create_fun(
                                inv_line, student, partner_id
                            )
                            inv_ids.append(int(inv_id[0]))

                    # Separate invoice should be generated based on the
                    # same Terms and different invoices date
                    if check_term and check_date == False:
                        if self.env.context.get("fee_line_wizard"):
                            fee_line = self.env.context.get("fee_line_wizard")
                            inv_id = self.separate_invoice_create_fun(
                                fee_line, student, partner_id
                            )
                        else:
                            # inv_line = (
                            #     self.env["xe.fees.details"]
                            #     .sudo()
                            #     .search(
                            #         [
                            #             ("invoice_date", "in", invoice_dates),
                            #             ("fee_structure_id", "=", self.id),
                            #             ("parent_state", "=", "draft"),
                            #             ("term", "=", term),
                            #         ]
                            #     )
                            # )
                            inv_id = self.separate_invoice_create_fun(
                                inv_line, student, partner_id
                            )
                        inv_ids.append(int(inv_id[0]))

                    # Single Invoice Generated based on same term and same invoice date for all line
                    if check_term and check_date:
                        # Invoice Created from admission wizard
                        if self.env.context.get("fee_line_wizard"):
                            fee_line = self.env.context.get("fee_line_wizard")
                            inv_id = self.separate_invoice_create_fun(
                                fee_line, student, partner_id
                            )
                        # Transport Logic Normal workflow
                        else:
                            # if student.fees_to_zone_id.id:
                            #     inv_line = (
                            #         self.env["xe.fees.details"]
                            #         .sudo()
                            #         .search(
                            #             [
                            #                 ("invoice_date", "in", invoice_dates),
                            #                 ("fee_structure_id", "=", self.id),
                            #                 ("fee_type", "=", student.fees_to_zone_id.id),
                            #                 ("parent_state", "=", "draft"),
                            #                 ("term", "=", term),
                            #             ]
                            #         )
                            #     )
                            # else:
                            #     inv_line = (
                            #         self.env["xe.fees.details"]
                            #         .sudo()
                            #         .search(
                            #             [
                            #                 ("invoice_date", "in", invoice_dates),
                            #                 ("fee_structure_id", "=", self.id),
                            #                 ("parent_state", "=", "draft"),
                            #                 ("term", "=", term),
                            #             ]
                            #         )
                            #     )
                            inv_id = self.separate_invoice_create_fun_new(
                                inv_line, student, partner_id
                            )
                        if inv_id:
                            inv_ids.append(int(inv_id[0]))

                # Single Invoice Generated based on same term and same invoice date for all line
                transport_wizard = self.env.context.get("fee_line_wizard")

                if single_inv:
                    if transport_wizard:
                        inv_ids = self.with_context(
                            single_inv=True
                        ).single_invoice_create_fun(student, partner_id, terms)
                    # else:
                    #     print('10')
                    #     inv_ids = self.with_context(generate_transport=True).single_invoice_create_fun(student, partner_id, terms)

                single_invtt = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("xe_fees_management.is_transport")
                )
                if single_invtt:
                    if student.fees_to_zone_id.id:
                        # inv_line = (
                        #     self.env["xe.fees.details"]
                        #     .sudo()
                        #     .search(
                        #         [
                        #             ("invoice_date", "in", invoice_dates),
                        #             ("fee_structure_id", "=", self.id),
                        #             ("fee_type", "=", student.fees_to_zone_id.id),
                        #             ("parent_state", "=", "draft"),
                        #             ("term", "=", term),
                        #         ]
                        #     )
                        # )
                        inv_id = self.separate_invoice_create_fun(
                            inv_line, student, partner_id
                        )
                        self.env["account.move"].search([("id", "=", inv_id)]).write(
                            {"fee_structu_type": "transport"}
                        )
                        if inv_ids is None:
                            inv_ids = []
                        inv_ids.append(int(inv_id[0]))

                # Invoice ID map with fees structure
                account_invoices = (
                    self.env["account.move"].sudo().search([("id", "in", inv_ids)])
                )
                if self.env.context.get("fee_line_wizard"):
                    account_invoices.write(
                        {
                            "is_application_invoice": True,
                            "fee_structu_type": "transport",
                        }
                    )
                    self.write({"invoice_ids": [(6, 0, account_invoices.ids)]})
                else:
                    self.write({"invoice_ids": [(6, 0, account_invoices.ids)]})
        return True

    # Generate Optional Button Logic
    def generate_optional(self):
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        single_inv = (
            self.env["ir.config_parameter"]
            .sudo()
            .search([("key", "=", "xe_fees_management.is_optional")], limit=1)
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            current_academic_year_id = academic_rec.id
        else:
            current_academic_year_id = self.academic_year_id.id
        # Fetch the student record based on current academic year
        student_rec = self.env.context.get("student_rec")
        term = self.env.context.get("term_id")
        course = self.course_id.ids
        classroom = self.classroom_id.ids
        student_domain = [("current_academic_year_id", "=", current_academic_year_id)]
        if course:
            student_domain.append(("course_id", "in", course))
        if classroom:
            student_domain.append(("classroom_id", "in", classroom))
        if not student_rec:
            student_domain.append(("is_optional", "=", True))
            student_rec = self.env["xe.student"].search(student_domain)

        inv_ids = []
        if self.is_include_optional_fees:
            for i in student_rec:
                inv_lines = self.env["xe.fees.details"]
                partner_id = i.partner_id
                student = i
                terms = self.fee_details_ids.mapped("term_id")
                invoice_dates = self.fee_details_ids.mapped("invoice_date")
                check_term = all(x == terms[0] for x in terms)
                check_date = all(x == invoice_dates[0] for x in invoice_dates)
                if student.is_optional:
                    for act in student.optional_fee_ids:
                        inv_line_one = self.env["xe.fees.details"].create(
                            {
                                "invoice_date": self.invoice_date,
                                "fee_type_id": act.id,
                                "term_id": self.term_id.id,
                                "parent_state": "draft",
                                "amount": act.product_id.list_price,
                            }
                        )
                        inv_lines += inv_line_one

                    if not single_inv:
                        # Separate invoice should be generated based on the different Terms
                        if check_term == False:
                            # for i in terms:
                            # inv_line = (
                            #     self.env["xe.fees.details"]
                            #     .sudo()
                            #     .search(
                            #         [
                            #             ("term", "=", term),
                            #             ("fee_structure_id", "=", self.id),
                            #             ("parent_state", "=", "draft"),
                            #         ]
                            #     )
                            # )
                            for inv_line in inv_lines:
                                inv_id = self.separate_invoice_create_fun(
                                    inv_line, student, partner_id
                                )
                                inv_ids.append(int(inv_id[0]))

                        # Separate invoice should be generated based on the
                        # same Terms and different invoices date
                        if check_term and check_date == False:
                            # inv_line = (
                            #     self.env["xe.fees.details"]
                            #     .sudo()
                            #     .search(
                            #         [
                            #             ("invoice_date", "in", invoice_dates),
                            #             ("fee_structure_id", "=", self.id),
                            #             ("parent_state", "=", "draft"),
                            #             ("term", "=", term),
                            #         ]
                            #     )
                            # )
                            for inv_line in inv_lines:
                                inv_id = self.separate_invoice_create_fun(
                                    inv_line, student, partner_id
                                )
                                inv_ids.append(int(inv_id[0]))

                        # Single Invoice Generated based on same term and same invoice date for all line
                        if check_term and check_date:
                            # if student.optional_fee_ids.ids:
                            #     inv_line = (
                            #         self.env["xe.fees.details"]
                            #         .sudo()
                            #         .search(
                            #             [
                            #                 ("invoice_date", "in", invoice_dates),
                            #                 ("fee_structure_id", "=", self.id),
                            #                 ("fee_type", "in", student.optional_fee_ids.ids),
                            #                 ("parent_state", "=", "draft"),
                            #                 ("term", "=", term),
                            #             ]
                            #         )
                            #     )
                            # else:
                            #     inv_line = (
                            #         self.env["xe.fees.details"]
                            #         .sudo()
                            #         .search(
                            #             [
                            #                 ("invoice_date", "in", invoice_dates),
                            #                 ("fee_structure_id", "=", self.id),
                            #                 ("parent_state", "=", "draft"),
                            #                 ("term", "=", term),
                            #             ]
                            #         )
                            #     )
                            for inv_line in inv_lines:
                                # inv_id = self.separate_invoice_create_fun(
                                #     inv_line, student, partner_id
                                # )
                                inv_id = self.separate_invoice_create_fun_new(
                                    inv_line, student, partner_id
                                )
                                if inv_id:
                                    inv_ids.append(int(inv_id[0]))

                # Single Invoice Generated based on same term and same invoice date for all line
                if single_inv:
                    inv_ids = self.single_invoice_create_fun(student, partner_id, terms)

                single_invop = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("xe_fees_management.is_optional")
                )
                if single_invop:
                    if student.optional_fee_ids:
                        # inv_line = (
                        #     self.env["xe.fees.details"]
                        #     .sudo()
                        #     .search(
                        #         [
                        #             ("invoice_date", "in", invoice_dates),
                        #             ("fee_structure_id", "=", self.id),
                        #             ("fee_type", "=", student.optional_fee_ids.id),
                        #             ("parent_state", "=", "draft"),
                        #             ("term", "=", term),
                        #         ]
                        #     )
                        # )
                        # for inv_line in inv_lines:
                        inv_id = self.separate_invoice_create_fun(
                            inv_lines, student, partner_id
                        )
                        self.env["account.move"].search([("id", "=", inv_id)]).write(
                            {"fee_structu_type": "optional"}
                        )
                        if inv_ids is None:
                            inv_ids = []
                        inv_ids.append(int(inv_id[0]))

                # Invoice ID map with fees structure
                account_invoices = (
                    self.env["account.move"].sudo().search([("id", "in", inv_ids)])
                )
                if self.env.context.get("fee_line_wizard"):
                    account_invoices.write(
                        {"is_application_invoice": True, "fee_structu_type": "optional"}
                    )
                    self.write({"invoice_ids": [(6, 0, account_invoices.ids)]})
                else:
                    self.write({"invoice_ids": [(6, 0, account_invoices.ids)]})
        return True

    # generate button logic added by activity
    def generate_activity(self):
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        single_inv_act = (
            self.env["ir.config_parameter"]
            .sudo()
            .search([("key", "=", "xe_fees_management.is_activity")], limit=1)
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            current_academic_year_id = academic_rec.id
        else:
            current_academic_year_id = self.academic_year_id.id
        # Fetch the student record based on current academic year
        student_rec = self.env.context.get("student_rec")
        activity_fee_wizard = self.env.context.get("activity_fee_wizard")
        term = self.env.context.get("term_id")
        course = self.course_id.ids
        classroom = self.classroom_id.ids
        student_domain = [("current_academic_year_id", "=", current_academic_year_id)]
        if course:
            student_domain.append(("course_id", "in", course))
        if classroom:
            student_domain.append(("classroom_id", "in", classroom))
        if not student_rec:
            student_domain.append(("is_activity", "=", True))
            student_rec = self.env["xe.student"].search(student_domain)

        inv_ids = []
        for i in student_rec:
            inv_lines = self.env["xe.fees.details"]
            partner_id = i.partner_id
            student = i
            terms = self.fee_details_ids.mapped("term_id")
            invoice_dates = self.fee_details_ids.mapped("invoice_date")
            check_term = all(x == terms[0] for x in terms)
            check_date = all(x == invoice_dates[0] for x in invoice_dates)
            if student.is_activity:
                for act in student.activity_fee_ids:
                    inv_line_one = self.env["xe.fees.details"].create(
                        {
                            "invoice_date": self.invoice_date,
                            "fee_type_id": act.id,
                            "fee_type": act.id,
                            "term_id": self.term_id.id,
                            "parent_state": "draft",
                            "amount": act.product_id.list_price,
                        }
                    )
                    inv_lines += inv_line_one
                if not single_inv_act:
                    # Separate invoice should be generated based on the different Terms
                    if check_term == False:
                        if student.is_activity and student.activity_fee_ids:
                            # inv_line = (
                            #     self.env["xe.fees.details"]
                            #     .sudo()
                            #     .search(
                            #         [
                            #             ("term", "=", i.id),
                            #             ("fee_structure_id", "=", self.id),
                            #             ("fee_type", "in", student.activity_fee_ids.ids),
                            #             ("parent_state", "=", "draft"),
                            #             ("term", "=", term),
                            #         ]
                            #     )
                            # )
                            for inv_line in inv_lines:
                                inv_id = self.separate_invoice_create_fun(
                                    inv_line, student, partner_id
                                )
                                inv_ids.append(int(inv_id[0]))

                    # Separate invoice should be generated based on the
                    # same Terms and different invoices date
                    # if check_term and check_date == False:
                    #     inv_line = (
                    #         self.env["xe.fees.details"]
                    #         .sudo()
                    #         .search(
                    #             [
                    #                 ("invoice_date", "in", invoice_dates),
                    #                 ("fee_structure_id", "=", self.id),
                    #                 ("parent_state", "=", "draft"),
                    #                 ("term", "=", term),
                    #             ]
                    #         )
                    #     )
                    #     for i in inv_line:
                    #         for j in student.activity_fee_ids:
                    #             if i.fee_type_id.id == j.id:
                    #                 if activity_fee_wizard:
                    #                     inv_id = self.with_context(
                    #                         activity_fee_wizard=activity_fee_wizard
                    #                     ).separate_invoice_create_fun(
                    #                         inv_line, student, partner_id
                    #                     )
                    #                 else:
                    #                     inv_id = self.separate_invoice_create_fun(
                    #                         i, student, partner_id
                    #                     )
                    #                 inv_ids.append(int(inv_id[0]))

                    # Single Invoice Generated based on same term and same invoice date for all line
                    if check_term and check_date:
                        if student.is_activity and student.activity_fee_ids:
                            # inv_line = (
                            #     self.env["xe.fees.details"]
                            #     .sudo()
                            #     .search(
                            #         [
                            #             ("invoice_date", "in", invoice_dates),
                            #             ("fee_structure_id", "=", self.id),
                            #             ("fee_type", "in", student.activity_fee_ids.ids),
                            #             ("parent_state", "=", "draft"),
                            #             ("term", "=", term),
                            #         ]
                            #     )
                            # )
                            for inv_line in inv_lines:
                                if activity_fee_wizard:
                                    inv_id = self.with_context(
                                        activity_fee_wizard=activity_fee_wizard
                                    ).separate_invoice_create_fun(
                                        inv_line, student, partner_id
                                    )
                                else:
                                    inv_id = self.separate_invoice_create_fun_new(
                                        inv_line, student, partner_id
                                    )
                                if inv_id:
                                    inv_ids.append(int(inv_id[0]))

                # Single Invoice Generated based on same term and same invoice date for all line
                if single_inv_act:
                    inv_ids = self.single_invoice_create_fun(student, partner_id, terms)

                single_invat = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("xe_fees_management.is_activity")
                )
                if single_invat:
                    if student.activity_fee_ids:
                        # inv_line = (
                        #     self.env["xe.fees.details"]
                        #     .sudo()
                        #     .search(
                        #         [
                        #             ("invoice_date", "in", invoice_dates),
                        #             ("fee_structure_id", "=", self.id),
                        #             ("fee_type", "=", student.activity_fee_ids.id),
                        #             ("parent_state", "=", "draft"),
                        #             ("term", "=", term),
                        #         ]
                        #     )
                        # )
                        # for inv_line in inv_lines:
                        inv_id = self.separate_invoice_create_fun(
                            inv_lines, student, partner_id
                        )
                        self.env["account.move"].search([("id", "=", inv_id)]).write(
                            {"fee_structu_type": "activity"}
                        )
                        if inv_ids is None:
                            inv_ids = []
                        inv_ids.append(int(inv_id[0]))

                # Invoice ID Map with fees structure
                account_invoices = (
                    self.env["account.move"].sudo().search([("id", "in", inv_ids)])
                )
                if self.env.context.get("activity_fee_wizard"):
                    account_invoices.write(
                        {"is_application_invoice": True, "fee_structu_type": "activity"}
                    )
                self.write({"invoice_ids": [(6, 0, account_invoices.ids)]})
        return True

    # Generate boarding fees logic
    def generate_boarding(self):
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        single_inv_board = (
            self.env["ir.config_parameter"]
            .sudo()
            .search([("key", "=", "xe_fees_management.is_boarding")], limit=1)
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            current_academic_year_id = academic_rec.id
        else:
            current_academic_year_id = self.academic_year_id.id
        # Fetch the student record based on current academic year
        student_rec = self.env.context.get("student_rec")
        boarding_fee_wizard = self.env.context.get("boarding_fee_wizard")
        term = self.env.context.get("term_id")
        course = self.course_id.ids
        classroom = self.classroom_id.ids
        student_domain = [("current_academic_year_id", "=", current_academic_year_id)]
        if course:
            student_domain.append(("course_id", "in", course))
        if classroom:
            student_domain.append(("classroom_id", "in", classroom))
        if not student_rec:
            student_domain.append(("is_boarding", "=", True))
            student_rec = self.env["xe.student"].search(student_domain)

        inv_ids = []
        for i in student_rec:
            partner_id = i.partner_id
            student = i
            terms = self.fee_details_ids.mapped("term_id")
            invoice_dates = self.fee_details_ids.mapped("invoice_date")
            check_term = all(x == terms[0] for x in terms)
            check_date = all(x == invoice_dates[0] for x in invoice_dates)

            if not single_inv_board:
                # Separate invoice should be generated based on the different Terms
                if check_term == False and student.is_boarding:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("term_id", "=", i.id),
                                ("fee_structure_id", "=", self.id),
                                ("parent_state", "=", "draft"),
                                ("term", "=", term),
                            ]
                        )
                    )
                    inv_id = self.separate_invoice_create_fun(
                        inv_line, student, partner_id
                    )
                    inv_ids.append(int(inv_id[0]))

                # Separate invoice should be generated based on the
                # same Terms and different invoices date
                if check_term and check_date == False:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", self.id),
                                ("parent_state", "=", "draft"),
                                ("term", "=", term),
                            ]
                        )
                    )
                    for i in inv_line:
                        inv_id = self.separate_invoice_create_fun(
                            i, student, partner_id
                        )
                        inv_ids.append(int(inv_id[0]))

                # Single Invoice Generated based on same term and same invoice date for all line
                if check_term and check_date and student.is_boarding:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", self.id),
                                ("parent_state", "=", "draft"),
                                ("term", "=", term),
                            ]
                        )
                    )
                    if boarding_fee_wizard:
                        inv_id = self.with_context(
                            boarding_fee_wizard=boarding_fee_wizard
                        ).separate_invoice_create_fun(inv_line, student, partner_id)
                    else:
                        inv_id = self.separate_invoice_create_fun(
                            inv_line, student, partner_id
                        )
                    if inv_id:
                        inv_ids.append(int(inv_id[0]))

            # Single Invoice Generated based on same term and same invoice date for all line
            if single_inv_board:
                inv_ids = self.single_invoice_create_fun(student, partner_id, terms)

            # Invoice ID map with fees structure
            account_invoices = (
                self.env["account.move"].sudo().search([("id", "in", inv_ids)])
            )
            if self.env.context.get("boarding_fee_wizard"):
                account_invoices.write(
                    {"is_application_invoice": True, "fee_structu_type": "boarding"}
                )
            self.write({"invoice_ids": [(6, 0, account_invoices.ids)]})
        return True

    # Generate Button Logic added Academic Fee
    def generate(self):
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            current_academic_year_id = academic_rec.id
        else:
            current_academic_year_id = self.academic_year_id.id
        course = self.course_id.ids
        classroom = self.classroom_id.ids
        student_domain = [("current_academic_year_id", "=", current_academic_year_id)]
        if course:
            student_domain.append(("course_id", "in", course))
        if classroom:
            student_domain.append(("classroom_id", "in", classroom))
        student_rec = self.env.context.get("student_rec")
        if not student_rec:
            student_rec = self.env["xe.student"].search(student_domain)
        if self.env.context.get("student_rec"):
            student_rec = self.env.context.get("student_rec")
        term = self.env.context.get("term_id")
        if not student_rec:
            raise ValidationError(
                _("Sorry, There is no matching student for this academic year.")
            )
        inv_ids = []
        for i in student_rec:
            partner_id = i.partner_id
            student = i
            terms = self.fee_details_ids.mapped("term_id")
            invoice_dates = self.fee_details_ids.mapped("invoice_date")
            check_term = all(x == terms[0] for x in terms)
            check_date = all(x == invoice_dates[0] for x in invoice_dates)
            if term:
                terms = self.env["xe.academic.terms"].browse(term)
            # Separate invoice should be generated based on the different Terms
            if not check_term:
                if self._context.get("academic_fee_wizard"):
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", self.id),
                                ("parent_state", "=", "draft"),
                                ("term", "=", term),
                            ]
                        )
                    )
                else:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", self.id),
                                ("fee_type_id.duration", "!=", "admissiontime"),
                                ("parent_state", "=", "draft"),
                                ("term", "=", term),
                            ]
                        )
                    )
                inv_id = self.separate_invoice_create_fun(inv_line, student, partner_id)
                inv_ids.append(int(inv_id[0]))

            # Separate invoice should be generated based on the
            # same Terms and different invoices date
            if check_term and check_date == False:
                if self._context.get("academic_fee_wizard"):
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", self.id),
                                ("parent_state", "=", "draft"),
                                ("term", "=", term),
                            ]
                        )
                    )
                else:
                    inv_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("invoice_date", "in", invoice_dates),
                                ("fee_structure_id", "=", self.id),
                                ("fee_type_id.duration", "!=", "admissiontime"),
                                ("parent_state", "=", "draft"),
                                ("term", "=", term),
                            ]
                        )
                    )
                inv_id = self.separate_invoice_create_fun(inv_line, student, partner_id)
                inv_ids.append(int(inv_id[0]))

            # Single Invoice Generated based on same term and same invoice date for all line
            if check_term and check_date:
                if self._context.get("academic_fee_wizard"):
                    inv_ids = self.with_context(
                        academic_fee_wizard=True
                    ).single_invoice_create_fun(student, partner_id, terms)
                else:
                    inv_ids = self.with_context(
                        generate=True
                    ).single_invoice_create_fun(student, partner_id, terms)

            # remove line from invoice if separate invoice is true
            for inv in self.env["account.move"].sudo().search([("id", "in", inv_ids)]):
                single_invtt = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("xe_fees_management.is_transport")
                )
                single_invat = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("xe_fees_management.is_activity")
                )
                single_invop = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("xe_fees_management.is_optional")
                )
                if single_invtt:
                    trans_line = self.fee_details_ids.filtered(
                        lambda r: r.fee_type_id.type == "transport"
                    )
                    del_line = inv.invoice_line_ids.filtered(
                        lambda r: r.name == trans_line.fee_type_id.product_id.name
                    )
                    inv.write({"invoice_line_ids": [(2, r.id) for r in del_line]})
                if single_invat:
                    at_line = self.fee_details_ids.filtered(
                        lambda r: r.fee_type_id.type == "activity"
                    )
                    del_line = inv.invoice_line_ids.filtered(
                        lambda r: r.name == at_line.fee_type_id.product_id.name
                    )
                    inv.write({"invoice_line_ids": [(2, r.id) for r in del_line]})
                if single_invop:
                    op_line = self.fee_details_ids.filtered(
                        lambda r: r.fee_type_id.type == "optional"
                    )
                    del_line = inv.invoice_line_ids.filtered(
                        lambda r: r.name == op_line.fee_type_id.product_id.name
                    )
                    inv.write({"invoice_line_ids": [(2, r.id) for r in del_line]})

            # Invoice ID map with fees structure
            account_invoices = (
                self.env["account.move"].sudo().search([("id", "in", inv_ids)])
            )
            if self.env.context.get("academic_fee_wizard"):
                account_invoices.write(
                    {"is_application_invoice": True, "fee_structu_type": "academic"}
                )
            self.write({"invoice_ids": [(6, 0, account_invoices.ids)]})
        return True

    def separate_invoice_create_fun_new(self, inv_line, student, partner_id):
        av_inv = self.env["account.move"].search(
            [
                ("partner_id", "=", partner_id.id),
                ("course_id", "=", student.course_id.id),
                ("class_room_id", "=", student.classroom_id.id),
                ("state", "=", "draft"),
                ("fee_structu_type", "=", "academic"),
            ]
        )
        if av_inv:
            invoice_line_ids = []
            account_id = False
            product_temp = (
                self.env["product.template"]
                .sudo()
                .search([("id", "=", inv_line.fee_type_id.product_id.id)], limit=1)
            )
            product = product_temp.product_variant_id
            if product.property_account_income_id:
                account_id = product.property_account_income_id.id
            if not account_id:
                account_id = product.categ_id.property_account_income_categ_id.id
            if not account_id:
                raise UserError(
                    _('There is no income account defined for this product: "%s"')
                    % product.name
                )
            inv_line_vals = self.create_invoice_line_values(
                account_id, product, inv_line
            )
            invoice_line_ids.append([0, 0, inv_line_vals])
            av_inv.write({"invoice_line_ids": invoice_line_ids})
        else:
            self.separate_invoice_create_fun(inv_line, student, partner_id)

    # Invoice Created manually based on different date and term, same term and different date
    def separate_invoice_create_fun(self, inv_line, student, partner_id):
        account_move_rec = False
        if self.env.context.get("activity_fee_wizard"):
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("is_application_invoice", "=", True),
                        ("fee_structu_type", "in", ["activity"]),
                    ],
                    limit=1,
                )
            )
        elif self.env.context.get("boarding_fee_wizard"):
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("is_application_invoice", "=", True),
                        ("fee_structu_type", "in", ["boarding"]),
                    ],
                    limit=1,
                )
            )
        if not account_move_rec:
            inv_list = []
            invoice_line_ids = []
            invoice_date = False
            term = False
            for line in inv_line:
                invoice_date = line.invoice_date
                # term = line.term.name
                account_id = False
                product_temp = (
                    self.env["product.template"]
                    .sudo()
                    .search([("id", "=", line.fee_type_id.product_id.id)], limit=1)
                )
                product = product_temp.product_variant_id
                if product.property_account_income_id:
                    account_id = product.property_account_income_id.id
                if not account_id:
                    account_id = product.categ_id.property_account_income_categ_id.id
                if not account_id:
                    raise UserError(
                        _('There is no income account defined for this product: "%s"')
                        % product.name
                    )

                inv_line_vals = self.create_invoice_line_values(
                    account_id, product, line
                )
                invoice_line_ids.append([0, 0, inv_line_vals])

            is_transport_fees = is_activity = is_optional = is_boarding = False
            fee_rec = (
                self.env["xe.fees.details"]
                .sudo()
                .search(
                    [("id", "in", inv_line.ids), ("parent_state", "=", "draft")],
                    limit=1,
                )
            )
            if fee_rec.is_transport_fees:
                is_transport_fees = True
            elif fee_rec.is_activity:
                is_activity = True
            elif fee_rec.is_optional:
                is_optional = True
            elif fee_rec.is_boarding:
                is_boarding = True

            invoice_vals = self.get_invoice_vals(student, partner_id, invoice_line_ids)
            invoice = self.env["account.move"].sudo().create(invoice_vals)
            if term:
                term = str(term)
            invoice.write(
                {
                    "invoice_date": invoice_date or self.invoice_date,
                    "terms": term or student.term_id.name or self.term_id.name or False,
                    "roll_number": student.roll_number,
                    "course_id": student.course_id.id,
                    "class_room_id": student.classroom_id.id,
                    "is_transport_fees": is_transport_fees,
                    "is_optional": is_optional,
                    "is_activity": is_activity,
                    "is_boarding": is_boarding,
                    # "term_id": student.term_id.id,
                    "partner_id": partner_id.id,
                }
            )
            self.invoice_id = invoice.id
            invoice_line_ids.clear()
            inv_list.append(invoice.id)

            return inv_list

    # Single Invoice Create Based On same term, same invoice data
    # and configuration setting checkbox enable
    def single_invoice_create_fun(self, student, partner_id, terms):
        inv_list = []
        invoice_line_ids = []
        if self._context.get("inv_line"):
            fee_line_ids = self._context.get("inv_line")
        elif self._context.get("academic_fee_wizard"):
            fee_line_ids = self.fee_details_ids
        else:
            fee_line_ids = self.fee_details_ids.filtered(
                lambda line: line.fee_type_id.duration != "admissiontime"
            )
        # Transport Single Invoice from admission window
        single_inv = self.env.context.get("single_inv")
        if single_inv:
            fee_line_ids = (
                self.env["xe.fees.details"]
                .sudo()
                .search(
                    [
                        ("fee_type_id", "=", student.fees_to_zone_id.id),
                        ("parent_state", "=", "draft"),
                    ]
                )
            )
            # Academic Invoice Exist, Check the state as 'draft'.
            # Compare the student transport fees and fee structure fee type
            # both invoice date as same, Fees Line can we update the existing academic invoice.
            move_obj = (
                self.env["account.move"]
                .sudo()
                .search(
                    [("partner_id", "=", partner_id.id), ("state", "=", "draft")],
                    limit=1,
                )
            )
            # Student Transport fee and academic invoice date are same,
            # update the fee to existing invoice
            if fee_line_ids.filtered(
                lambda line: line.invoice_date == move_obj.invoice_date
            ):
                for line in fee_line_ids:
                    if line.invoice_date == move_obj.invoice_date:
                        account_id = False
                        product_temp = (
                            self.env["product.template"]
                            .sudo()
                            .search(
                                [("id", "=", line.fee_type_id.product_id.id)], limit=1
                            )
                        )
                        product = product_temp.product_variant_id
                        if product.property_account_income_id:
                            account_id = product.property_account_income_id.id
                        if not account_id:
                            account_id = (
                                product.categ_id.property_account_income_categ_id.id
                            )
                        if not account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s"'
                                )
                                % product.name
                            )
                        inv_line_vals = self.create_invoice_line_values(
                            account_id, product, line
                        )
                        invoice_line_ids.append([0, 0, inv_line_vals])

                if move_obj:
                    move_obj.write(
                        {
                            "invoice_line_ids": invoice_line_ids,
                            "invoice_date": line.invoice_date,
                            "terms": str(terms[0].name),
                            "fee_structu_type": self.fee_structu_type,
                            "course_id": student.course_id.id,
                            "class_room_id": student.classroom_id.id,
                            "roll_number": student.roll_number,
                        }
                    )
                    move_obj.partner_id.write({"invoice_ids": [(6, 0, move_obj.ids)]})
                    student.write({"invoice_ids": [(6, 0, move_obj.ids)]})
                    move_obj.fee_name = str(self.name) + "-" + str(terms[0].name)
                    self.invoice_id = move_obj.id
                    inv_list.append(move_obj.id)
                    return inv_list
        # Academic Invoice Creation
        # if self.fee_structu_type == "academic":
        if self.fee_details_ids.filtered(
            lambda r: r.fee_type_id.type == "academic"
        ) and self.env.context.get("generate"):
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("is_application_invoice", "=", True),
                    ],
                    limit=1,
                )
            )
            if not account_move_rec:
                move_obj = (
                    self.env["account.move"]
                    .sudo()
                    .search(
                        [
                            ("partner_id", "=", partner_id.id),
                            ("is_academic", "=", True),
                        ],
                        limit=1,
                    )
                )
                invoice_date = False
                for line in fee_line_ids:
                    invoice_date = line.invoice_date
                    account_id = False
                    product_temp = (
                        self.env["product.template"]
                        .sudo()
                        .search([("id", "=", line.fee_type_id.product_id.id)], limit=1)
                    )
                    product = product_temp.product_variant_id
                    if product.property_account_income_id:
                        account_id = product.property_account_income_id.id
                    if not account_id:
                        account_id = (
                            product.categ_id.property_account_income_categ_id.id
                        )
                    if not account_id:
                        raise UserError(
                            _(
                                'There is no income account defined for this product: "%s"'
                            )
                            % product.name
                        )
                    inv_line_vals = self.create_invoice_line_values(
                        account_id, product, line
                    )
                    invoice_line_ids.append([0, 0, inv_line_vals])

                invoice_vals = self.get_invoice_vals(
                    student, partner_id, invoice_line_ids
                )
                invoice = self.env["account.move"].sudo().create(invoice_vals)
                student.write({"invoice_ids": [(6, 0, invoice.ids)]})
                invoice.write(
                    {
                        "invoice_date": invoice_date,
                        "fee_name": str(self.name) + "-" + str(terms[0].name),
                        "terms": str(terms[0].name),
                        "fee_structu_type": self.fee_structu_type,
                        "is_academic": True,
                        "fee_structu_id": self.id,
                        "course_id": student.course_id.id,
                        "class_room_id": student.classroom_id.id,
                        "roll_number": student.roll_number,
                    }
                )
                self.invoice_id = invoice.id
                inv_list.append(invoice.id)
                return inv_list

        # Optional Fee Invoice creation
        # elif self.fee_structu_type == "optional":
        if self.fee_structu_type == "optional":
            # Academic Invoice Exist, Check the state as 'draft'.
            # Compare the student Optional fees and fee structure fee type both
            # invoice date as same, Fees Line can we update the existing academic invoice.
            move_obj = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("state", "=", "draft"),
                        ("is_academic", "=", True),
                    ],
                    limit=1,
                )
            )

            # Student Optional fee and academic invoice date are same,
            # update the fee to existing invoice
            if fee_line_ids.filtered(
                lambda line: line.invoice_date == move_obj.invoice_date
            ):
                for line in fee_line_ids.filtered(
                    lambda line: line.invoice_date == move_obj.invoice_date
                ):
                    if line.fee_type_id.id in student.optional_fee_ids.ids:
                        account_id = False
                        product_temp = (
                            self.env["product.template"]
                            .sudo()
                            .search(
                                [("id", "=", line.fee_type_id.product_id.id)], limit=1
                            )
                        )
                        product = product_temp.product_variant_id
                        if product.property_account_income_id:
                            account_id = product.property_account_income_id.id
                        if not account_id:
                            account_id = (
                                product.categ_id.property_account_income_categ_id.id
                            )
                        if not account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s"'
                                )
                                % product.name
                            )
                        inv_line_vals = self.create_invoice_line_values(
                            account_id, product, line
                        )
                        invoice_line_ids.append([0, 0, inv_line_vals])

                if move_obj:
                    move_obj.write(
                        {
                            "invoice_line_ids": invoice_line_ids,
                            "invoice_date": line.invoice_date,
                            "terms": str(terms[0].name),
                            "fee_structu_id": self.id,
                            "is_optional": True,
                            "course_id": student.course_id.id,
                            "class_room_id": student.classroom_id.id,
                            "roll_number": student.roll_number,
                        }
                    )
                    move_obj.partner_id.write({"invoice_ids": [(6, 0, move_obj.ids)]})
                    student.write({"invoice_ids": [(6, 0, move_obj.ids)]})
                    move_obj.fee_name = str(self.name) + "-" + str(terms[0].name)
                    self.invoice_id = move_obj.id
                    inv_list.append(move_obj.id)
                    return inv_list

            # Student Optional fee and academic invoice date are different, Created a new invoice
            if fee_line_ids.filtered(
                lambda line: line.invoice_date != move_obj.invoice_date
            ):
                for line in fee_line_ids.filtered(
                    lambda line: line.invoice_date != move_obj.invoice_date
                ):
                    if line.fee_type_id.id in student.optional_fee_ids.ids:
                        move_obj = (
                            self.env["account.move"]
                            .sudo()
                            .search(
                                [
                                    ("partner_id", "=", partner_id.id),
                                    ("invoice_date", "=", line.invoice_date),
                                    ("state", "=", "draft"),
                                ],
                                limit=1,
                            )
                        )
                        if move_obj and move_obj.state == "draft":
                            return []
                        else:
                            if move_obj.invoice_date == line.invoice_date:
                                account_id = False
                                product_temp = (
                                    self.env["product.template"]
                                    .sudo()
                                    .search(
                                        [("id", "=", line.fee_type_id.product_id.id)],
                                        limit=1,
                                    )
                                )
                                product = product_temp.product_variant_id
                                if product.property_account_income_id:
                                    account_id = product.property_account_income_id.id
                                if not account_id:
                                    account_id = (
                                        product.categ_id.property_account_income_categ_id.id
                                    )
                                if not account_id:
                                    raise UserError(
                                        _(
                                            'There is no income account defined for this product: "%s"'
                                        )
                                        % product.name
                                    )
                                inv_line_vals = self.create_invoice_line_values(
                                    account_id, product, line
                                )
                                invoice_line_ids.append([0, 0, inv_line_vals])
                                move_obj.write({"invoice_line_ids": invoice_line_ids})

                            invoice_date = line.invoice_date
                            account_id = False
                            product_temp = (
                                self.env["product.template"]
                                .sudo()
                                .search(
                                    [("id", "=", line.fee_type_id.product_id.id)],
                                    limit=1,
                                )
                            )
                            product = product_temp.product_variant_id
                            if product.property_account_income_id:
                                account_id = product.property_account_income_id.id
                            if not account_id:
                                account_id = (
                                    product.categ_id.property_account_income_categ_id.id
                                )
                            if not account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s"'
                                    )
                                    % product.name
                                )
                            inv_line_vals = self.create_invoice_line_values(
                                account_id, product, line
                            )
                            invoice_line_ids.append([0, 0, inv_line_vals])
                            invoice_vals = self.get_invoice_vals(
                                student, partner_id, invoice_line_ids
                            )
                            invoice = (
                                self.env["account.move"].sudo().create(invoice_vals)
                            )
                            student.write({"invoice_ids": [(6, 0, invoice.ids)]})
                            invoice.write(
                                {
                                    "invoice_date": invoice_date,
                                    "terms": str(terms[0].name),
                                    "fee_structu_id": self.id,
                                    "is_optional": True,
                                    "course_id": student.course_id.id,
                                    "class_room_id": student.classroom_id.id,
                                    "roll_number": student.roll_number,
                                }
                            )
                            self.invoice_id = invoice.id
                            inv_list.append(invoice.id)
                            return inv_list

                if move_obj:
                    invoice_vals = self.get_invoice_vals(
                        student, partner_id, invoice_line_ids
                    )
                    invoice = self.env["account.move"].sudo().create(invoice_vals)
                    student.write({"invoice_ids": [(6, 0, invoice.ids)]})
                    invoice.write(
                        {
                            "invoice_date": line.invoice_date,
                            "terms": str(terms[0].name),
                            "fee_structu_id": self.id,
                            "is_optional": True,
                            "course_id": student.course_id.id,
                            "class_room_id": student.classroom_id.id,
                            "roll_number": student.roll_number,
                        }
                    )
                    self.invoice_id = invoice.id
                    inv_list.append(invoice.id)
                    return inv_list

        # Transport Fee Invoice creation
        # elif self.fee_structu_type == "transport":
        if self.fee_details_ids.filtered(
            lambda r: r.fee_type_id.type == "transport"
        ) and self.env.context.get("generate_transport"):
            # Academic Invoice Exist, Check the state as 'draft'.
            # Compare the student Optional fees and fee structure fee type both
            # invoice date as same, Fees Line can we update the existing academic invoice.
            move_obj = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("state", "=", "draft"),
                        ("is_academic", "=", True),
                    ],
                    limit=1,
                )
            )

            # Student Transport fee and academic invoice date are same,
            # update the fee to existing invoice
            # if fee_line_ids.filtered(
            #     lambda line: line.invoice_date == move_obj.invoice_date
            # ):
            #     for line in fee_line_ids.filtered(
            #         lambda line: line.invoice_date == move_obj.invoice_date
            #     ):
            #         if line.fee_type_id.id == student.fees_to_zone_id.id:
            #             account_id = False
            #             product_temp = (
            #                 self.env["product.template"]
            #                 .sudo()
            #                 .search([("id", "=", line.fee_type_id.product_id.id)], limit=1)
            #             )
            #             product = product_temp.product_variant_id
            #             if product.property_account_income_id:
            #                 account_id = product.property_account_income_id.id
            #             if not account_id:
            #                 account_id = (
            #                     product.categ_id.property_account_income_categ_id.id
            #                 )
            #             if not account_id:
            #                 raise UserError(
            #                     _(
            #                         'There is no income account defined for this product: "%s"'
            #                     )
            #                     % product.name
            #                 )
            #             inv_line_vals = self.create_invoice_line_values(
            #                 account_id, product, line
            #             )
            #             invoice_line_ids.append([0, 0, inv_line_vals])
            #     if move_obj:
            #         move_obj.write(
            #             {
            #                 "invoice_line_ids": invoice_line_ids,
            #                 "invoice_date": line.invoice_date,
            #                 "terms": str(terms[0].name),
            #                 "fee_structu_id": self.id,
            #                 "is_transport_fees": True,
            #                 "course_id": student.course_id.id,
            #                 "class_room_id": student.classroom_id.id,
            #                 "roll_number": student.roll_number,
            #             }
            #         )
            #         move_obj.partner_id.write({"invoice_ids": [(6, 0, move_obj.ids)]})
            #         student.write({"invoice_ids": [(6, 0, move_obj.ids)]})
            #         move_obj.fee_name = str(self.name) + "-" + str(terms[0].name)
            #         self.invoice_id = move_obj.id
            #         inv_list.append(move_obj.id)
            #         return inv_list

            # Student Transport fee and academic invoice date are different, Created a new invoice
            # if fee_line_ids.filtered(
            #     lambda line: line.invoice_date != move_obj.invoice_date
            # ):
            # for line in fee_line_ids.filtered(
            #     lambda line: line.invoice_date != move_obj.invoice_date
            # ):
            if fee_line_ids:
                for line in fee_line_ids:
                    if line.fee_type_id.id == student.fees_to_zone_id.id:
                        move_obj = (
                            self.env["account.move"]
                            .sudo()
                            .search(
                                [
                                    ("partner_id", "=", partner_id.id),
                                    ("invoice_date", "=", line.invoice_date),
                                    ("state", "=", "draft"),
                                ],
                                limit=1,
                            )
                        )
                        if move_obj and move_obj.state == "draft":
                            return []
                        else:
                            # if move_obj.invoice_date == line.invoice_date:
                            account_id = False
                            product_temp = (
                                self.env["product.template"]
                                .sudo()
                                .search(
                                    [("id", "=", line.fee_type_id.product_id.id)],
                                    limit=1,
                                )
                            )
                            product = product_temp.product_variant_id
                            if product.property_account_income_id:
                                account_id = product.property_account_income_id.id
                            if not account_id:
                                account_id = (
                                    product.categ_id.property_account_income_categ_id.id
                                )
                            if not account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s"'
                                    )
                                    % product.name
                                )
                            inv_line_vals = self.create_invoice_line_values(
                                account_id, product, line
                            )
                            invoice_line_ids.append([0, 0, inv_line_vals])
                            move_obj.write({"invoice_line_ids": invoice_line_ids})

                            invoice_date = line.invoice_date
                            account_id = False
                            product_temp = (
                                self.env["product.template"]
                                .sudo()
                                .search(
                                    [("id", "=", line.fee_type_id.product_id.id)],
                                    limit=1,
                                )
                            )
                            product = product_temp.product_variant_id
                            if product.property_account_income_id:
                                account_id = product.property_account_income_id.id
                            if not account_id:
                                account_id = (
                                    product.categ_id.property_account_income_categ_id.id
                                )
                            if not account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s"'
                                    )
                                    % product.name
                                )
                            inv_line_vals = self.create_invoice_line_values(
                                account_id, product, line
                            )
                            invoice_line_ids.append([0, 0, inv_line_vals])
                            invoice_vals = self.get_invoice_vals(
                                student, partner_id, invoice_line_ids
                            )
                            invoice = (
                                self.env["account.move"].sudo().create(invoice_vals)
                            )
                            student.write({"invoice_ids": [(6, 0, invoice.ids)]})
                            invoice.write(
                                {
                                    "invoice_date": invoice_date,
                                    "terms": str(terms[0].name),
                                    "fee_structu_id": self.id,
                                    "is_transport_fees": True,
                                    "course_id": student.course_id.id,
                                    "class_room_id": student.classroom_id.id,
                                    "roll_number": student.roll_number,
                                }
                            )
                            self.invoice_id = invoice.id
                            inv_list.append(invoice.id)
                            return inv_list
                if move_obj:
                    invoice_vals = self.get_invoice_vals(
                        student, partner_id, invoice_line_ids
                    )
                    invoice = self.env["account.move"].sudo().create(invoice_vals)
                    student.write({"invoice_ids": [(6, 0, invoice.ids)]})
                    invoice.write(
                        {
                            "invoice_date": line.invoice_date,
                            "terms": str(terms[0].name),
                            "fee_structu_id": self.id,
                            "is_transport_fees": True,
                            "course_id": student.course_id.id,
                            "class_room_id": student.classroom_id.id,
                            "roll_number": student.roll_number,
                        }
                    )
                    self.invoice_id = invoice.id
                    inv_list.append(invoice.id)
                    return inv_list

        # Activity Invoice creation
        # elif self.fee_structu_type == "activity":
        if self.fee_structu_type == "activity":
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("is_application_invoice", "=", True),
                        ("fee_structu_type", "in", ["activity"]),
                    ],
                    limit=1,
                )
            )
            if not account_move_rec:
                # Academic Invoice Exist, Check the state as 'draft'.
                # Compare the student transport fees and fee structure fee type both
                # invoice date as same, Fees Line can we update the existing academic invoice.
                move_obj = (
                    self.env["account.move"]
                    .sudo()
                    .search(
                        [
                            ("partner_id", "=", partner_id.id),
                            ("state", "=", "draft"),
                            ("is_academic", "=", True),
                        ],
                        limit=1,
                    )
                )

                # Student transport fee and academic invoice date are same,
                # update the fee to existing invoice
                if fee_line_ids.filtered(
                    lambda line: line.invoice_date == move_obj.invoice_date
                ):
                    for line in fee_line_ids.filtered(
                        lambda line: line.invoice_date == move_obj.invoice_date
                    ):
                        if line.fee_type_id.id in student.activity_fee_ids.ids:
                            account_id = False
                            product_temp = (
                                self.env["product.template"]
                                .sudo()
                                .search(
                                    [("id", "=", line.fee_type_id.product_id.id)],
                                    limit=1,
                                )
                            )
                            product = product_temp.product_variant_id
                            if product.property_account_income_id:
                                account_id = product.property_account_income_id.id
                            if not account_id:
                                account_id = (
                                    product.categ_id.property_account_income_categ_id.id
                                )
                            if not account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s"'
                                    )
                                    % product.name
                                )
                            inv_line_vals = self.create_invoice_line_values(
                                account_id, product, line
                            )
                            invoice_line_ids.append([0, 0, inv_line_vals])

                    if move_obj:
                        move_obj.write(
                            {
                                "invoice_line_ids": invoice_line_ids,
                                "invoice_date": line.invoice_date,
                                "terms": str(terms[0].name),
                                "fee_structu_id": self.id,
                                "is_activity": True,
                                "course_id": student.course_id.id,
                                "class_room_id": student.classroom_id.id,
                                "roll_number": student.roll_number,
                            }
                        )
                        move_obj.partner_id.write(
                            {"invoice_ids": [(6, 0, move_obj.ids)]}
                        )
                        student.write(
                            {
                                "invoice_ids": [(6, 0, move_obj.ids)],
                                "is_activity_invoice": True,
                            }
                        )
                        move_obj.fee_name = str(self.name) + "-" + str(terms[0].name)
                        self.invoice_id = move_obj.id
                        inv_list.append(move_obj.id)
                        return inv_list

                # Student transport fee and academic invoice date are different,
                # Created a new invoice
                if fee_line_ids.filtered(
                    lambda line: line.invoice_date != move_obj.invoice_date
                ):
                    for line in fee_line_ids.filtered(
                        lambda line: line.invoice_date != move_obj.invoice_date
                    ):
                        if line.fee_type_id.id in student.activity_fee_ids.ids:
                            move_obj = (
                                self.env["account.move"]
                                .sudo()
                                .search(
                                    [
                                        ("partner_id", "=", partner_id.id),
                                        ("invoice_date", "=", line.invoice_date),
                                        ("state", "=", "draft"),
                                    ],
                                    limit=1,
                                )
                            )
                            if move_obj and move_obj.state == "draft":
                                return []
                            else:
                                if move_obj.invoice_date == line.invoice_date:
                                    account_id = False
                                    product_temp = (
                                        self.env["product.template"]
                                        .sudo()
                                        .search(
                                            [
                                                (
                                                    "id",
                                                    "=",
                                                    line.fee_type_id.product_id.id,
                                                )
                                            ],
                                            limit=1,
                                        )
                                    )
                                    product = product_temp.product_variant_id
                                    if product.property_account_income_id:
                                        account_id = (
                                            product.property_account_income_id.id
                                        )
                                    if not account_id:
                                        account_id = (
                                            product.categ_id.property_account_income_categ_id.id
                                        )
                                    if not account_id:
                                        raise UserError(
                                            _(
                                                'There is no income account defined for this product: "%s"'
                                            )
                                            % product.name
                                        )
                                    inv_line_vals = self.create_invoice_line_values(
                                        account_id, product, line
                                    )
                                    invoice_line_ids.append([0, 0, inv_line_vals])
                                    move_obj.write(
                                        {"invoice_line_ids": invoice_line_ids}
                                    )

                                invoice_date = line.invoice_date
                                account_id = False
                                product_temp = (
                                    self.env["product.template"]
                                    .sudo()
                                    .search(
                                        [("id", "=", line.fee_type_id.product_id.id)],
                                        limit=1,
                                    )
                                )
                                product = product_temp.product_variant_id
                                if product.property_account_income_id:
                                    account_id = product.property_account_income_id.id
                                if not account_id:
                                    account_id = (
                                        product.categ_id.property_account_income_categ_id.id
                                    )
                                if not account_id:
                                    raise UserError(
                                        _(
                                            'There is no income account defined for this product: "%s"'
                                        )
                                        % product.name
                                    )
                                inv_line_vals = self.create_invoice_line_values(
                                    account_id, product, line
                                )
                                invoice_line_ids.append([0, 0, inv_line_vals])
                                invoice_vals = self.get_invoice_vals(
                                    student, partner_id, invoice_line_ids
                                )
                                invoice = (
                                    self.env["account.move"].sudo().create(invoice_vals)
                                )
                                student.write({"invoice_ids": [(6, 0, invoice.ids)]})
                                invoice.write(
                                    {
                                        "invoice_date": invoice_date,
                                        "terms": str(terms[0].name),
                                        "fee_structu_id": self.id,
                                        "course_id": student.course_id.id,
                                        "class_room_id": student.classroom_id.id,
                                        "roll_number": student.roll_number,
                                    }
                                )
                                self.invoice_id = invoice.id
                                inv_list.append(invoice.id)
                                return inv_list

                    if move_obj:
                        invoice_vals = self.get_invoice_vals(
                            student, partner_id, invoice_line_ids
                        )
                        invoice = self.env["account.move"].sudo().create(invoice_vals)
                        student.write(
                            {
                                "invoice_ids": [(6, 0, invoice.ids)],
                                "is_activity_invoice": True,
                            }
                        )
                        invoice.write(
                            {
                                "invoice_date": line.invoice_date,
                                "terms": str(terms[0].name),
                                "fee_structu_id": self.id,
                                "is_activity": True,
                                "course_id": student.course_id.id,
                                "class_room_id": student.classroom_id.id,
                                "roll_number": student.roll_number,
                            }
                        )
                        self.invoice_id = invoice.id
                        inv_list.append(invoice.id)
                        return inv_list

        # Boarding Invoice creation
        # elif self.fee_structu_type == "boarding":
        if self.fee_structu_type == "boarding":
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner_id.id),
                        ("is_application_invoice", "=", True),
                        ("fee_structu_type", "in", ["boarding"]),
                    ],
                    limit=1,
                )
            )
            if not account_move_rec:
                # Academic Invoice Exist, Check the state as 'draft'.
                # Compare the student Boarding fees and fee structure fee type both
                # invoice date as same, Fees Line can we update the existing academic invoice.
                move_obj = (
                    self.env["account.move"]
                    .sudo()
                    .search(
                        [
                            ("partner_id", "=", partner_id.id),
                            ("state", "=", "draft"),
                            ("is_academic", "=", True),
                        ],
                        limit=1,
                    )
                )

                # Student transport fee and academic invoice date are same,
                # update the fee to existing invoice
                if fee_line_ids.filtered(
                    lambda line: line.invoice_date == move_obj.invoice_date
                ):
                    for line in fee_line_ids.filtered(
                        lambda line: line.invoice_date == move_obj.invoice_date
                    ):
                        account_id = False
                        product_temp = (
                            self.env["product.template"]
                            .sudo()
                            .search(
                                [("id", "=", line.fee_type_id.product_id.id)], limit=1
                            )
                        )
                        product = product_temp.product_variant_id
                        if product.property_account_income_id:
                            account_id = product.property_account_income_id.id
                        if not account_id:
                            account_id = (
                                product.categ_id.property_account_income_categ_id.id
                            )
                        if not account_id:
                            raise UserError(
                                _(
                                    "There is no income account defined for this product: '%s'"
                                )
                                % product.name
                            )
                        inv_line_vals = self.create_invoice_line_values(
                            account_id, product, line
                        )
                        invoice_line_ids.append([0, 0, inv_line_vals])

                    if move_obj:
                        move_obj.write(
                            {
                                "invoice_line_ids": invoice_line_ids,
                                "invoice_date": line.invoice_date,
                                "fee_structu_id": self.id,
                                "is_boarding": True,
                                "course_id": student.course_id.id,
                                "class_room_id": student.classroom_id.id,
                            }
                        )
                        move_obj.partner_id.write(
                            {"invoice_ids": [(6, 0, move_obj.ids)]}
                        )
                        student.write(
                            {
                                "invoice_ids": [(6, 0, move_obj.ids)],
                                "is_boarding_invoice": True,
                            }
                        )
                        move_obj.fee_name = str(self.name) + "-" + str(terms[0].name)
                        self.invoice_id = move_obj.id
                        inv_list.append(move_obj.id)
                        return inv_list
                # Student transport fee and academic invoice date are different,
                # Created a new invoice
                if fee_line_ids.filtered(
                    lambda line: line.invoice_date != move_obj.invoice_date
                ):
                    for line in fee_line_ids.filtered(
                        lambda line: line.invoice_date != move_obj.invoice_date
                    ):
                        move_obj = (
                            self.env["account.move"]
                            .sudo()
                            .search(
                                [
                                    ("partner_id", "=", partner_id.id),
                                    ("invoice_date", "=", line.invoice_date),
                                    ("state", "=", "draft"),
                                ],
                                limit=1,
                            )
                        )
                        if move_obj and move_obj.state == "draft":
                            return []
                        else:
                            if move_obj.invoice_date == line.invoice_date:
                                account_id = False
                                product_temp = (
                                    self.env["product.template"]
                                    .sudo()
                                    .search(
                                        [("id", "=", line.fee_type_id.product_id.id)],
                                        limit=1,
                                    )
                                )
                                product = product_temp.product_variant_id
                                if product.property_account_income_id:
                                    account_id = product.property_account_income_id.id
                                if not account_id:
                                    account_id = (
                                        product.categ_id.property_account_income_categ_id.id
                                    )
                                if not account_id:
                                    raise UserError(
                                        _(
                                            'There is no income account defined for this product: "%s"'
                                        )
                                        % product.name
                                    )
                                inv_line_vals = self.create_invoice_line_values(
                                    account_id, product, line
                                )
                                invoice_line_ids.append([0, 0, inv_line_vals])
                                move_obj.write({"invoice_line_ids": invoice_line_ids})

                            invoice_date = line.invoice_date
                            account_id = False
                            product_temp = (
                                self.env["product.template"]
                                .sudo()
                                .search(
                                    [("id", "=", line.fee_type_id.product_id.id)],
                                    limit=1,
                                )
                            )
                            product = product_temp.product_variant_id
                            if product.property_account_income_id:
                                account_id = product.property_account_income_id.id
                            if not account_id:
                                account_id = (
                                    product.categ_id.property_account_income_categ_id.id
                                )
                            if not account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s"'
                                    )
                                    % product.name
                                )
                            inv_line_vals = self.create_invoice_line_values(
                                account_id, product, line
                            )
                            invoice_line_ids.append([0, 0, inv_line_vals])

                    if move_obj:
                        invoice_vals = self.get_invoice_vals(
                            student, partner_id, invoice_line_ids
                        )
                        invoice = self.env["account.move"].sudo().create(invoice_vals)
                        student.write(
                            {
                                "invoice_ids": [(6, 0, invoice.ids)],
                                "is_boarding_invoice": True,
                            }
                        )
                        invoice.write(
                            {
                                "invoice_date": invoice_date,
                                "fee_structu_id": self.id,
                                "is_boarding": True,
                                "course_id": student.course_id.id,
                                "class_room_id": student.classroom_id.id,
                            }
                        )
                        self.invoice_id = invoice.id
                        inv_list.append(invoice.id)
                        return inv_list
