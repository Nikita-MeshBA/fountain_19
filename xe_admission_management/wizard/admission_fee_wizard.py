# pylint: disable=E0401
import datetime

from odoo.exceptions import UserError

from odoo import api, fields, models, _


class AdmissionFeeWizard(models.TransientModel):
    _name = "admission.fee.wizard"
    _description = "Admission Fee Wizard"

    student_id = fields.Many2one("xe.student")
    course_id = fields.Many2one("xe.course", string="Class")
    classroom_id = fields.Many2one("xe.classroom", string="Class Room")
    current_academic_year_id = fields.Many2one("xe.academic.year")
    is_transport = fields.Boolean()
    is_activity = fields.Boolean()
    is_boarding = fields.Boolean()
    is_optional = fields.Boolean()
    due_days = fields.Integer()
    fees_to_zone_id = fields.Many2one("xe.fees.type", string="To Zone", tracking=True)
    activity_fee_ids = fields.Many2many("xe.fees.type")
    optional_fee_ids = fields.Many2many(
        "xe.fees.type", "fee_type_optional_wiz", "fee_id", "optional_id"
    )
    fee_details_ids = fields.One2many(
        "admn.fees.details.wizard",
        "fee_structure_wiz_id",
        string="Fees Details",
        tracking=True,
    )
    application_id = fields.Integer()
    term_id = fields.Many2one("xe.academic.terms", "Academic Term")

    @api.onchange("term_id")
    def _set_fees_detail_domain(self):
        for record in self:
            if record.term_id:
                invoice_line_ids = []
                # Add Academic Line
                fees_academic = (
                    self.env["xe.fees.structure"]
                    .sudo()
                    .search(
                        [
                            ("course_id", "=", record.course_id.id),
                            ("fee_structu_type", "=", "academic"),
                            (
                                "academic_year_id",
                                "=",
                                record.current_academic_year_id.id,
                            ),
                        ]
                    )
                )
                for fees in fees_academic:
                    for line in fees.fee_details_ids:
                        if line.term_id.id == record.term_id.id:
                            inv_line_vals = {
                                "fee_type_id": line.fee_type_id.id,
                                "term_id": line.term_id.id,
                                "amount": line.amount,
                                "invoice_date": line.invoice_date,
                                "due_date": line.due_date,
                                "schedule_date": line.schedule_date,
                                "receipt_name_id": line.receipt_name_id.id,
                                "fee_structure_id": fees_academic.id,
                                "fees_detail_id": line.id,
                                "academic_fee": True,
                            }
                            invoice_line_ids.append([0, 0, inv_line_vals])
                # Show transport line product
                if record.is_transport:
                    fee_details_line = (
                        self.env["xe.fees.details"]
                        .sudo()
                        .search(
                            [
                                ("fee_type_id", "=", record.fees_to_zone_id.id),
                                ("term_id", "=", record.term_id.id),
                            ]
                        )
                    )
                    for line in fee_details_line:
                        inv_line_vals = {
                            "fee_type_id": line.fee_type_id.id,
                            "term_id": line.term_id.id,
                            "amount": line.amount,
                            "invoice_date": line.invoice_date,
                            "due_date": line.due_date,
                            "schedule_date": line.schedule_date,
                            "receipt_name_id": line.receipt_name_id.id,
                            "fee_structure_id": fee_details_line.fee_structure_id.id,
                            "fees_detail_id": line.id,
                            "transport_fee": True,
                        }
                        invoice_line_ids.append([0, 0, inv_line_vals])

                # Show Activity line product
                if record.is_activity:
                    fees_struc = (
                        self.env["xe.fees.structure"]
                        .sudo()
                        .search(
                            [
                                ("is_activity", "=", self.is_activity),
                                ("company_id", "=", self.env.user.company_id.id),
                            ]
                        )
                    )
                    for fees in fees_struc:
                        for fees_line in fees.fee_details_ids:
                            if (
                                fees_line.fee_type_id.fee_type
                                in self.activity_fee_ids.mapped("fee_type")
                                and fees_line.term_id.id == record.term_id.id
                            ):
                                inv_line_vals = {
                                    "fee_type_id": fees_line.fee_type_id.id,
                                    "term_id": fees_line.term_id.id,
                                    "amount": fees_line.amount,
                                    "invoice_date": fees_line.invoice_date,
                                    "due_date": fees_line.due_date,
                                    "schedule_date": fees_line.schedule_date,
                                    "fee_structure_id": fees_struc.id,
                                    "receipt_name_id": fees_line.receipt_name_id.id,
                                    "fees_detail_id": fees_struc.id,
                                    "activity_fee": True,
                                }
                                invoice_line_ids.append([0, 0, inv_line_vals])

                # Show Optional line product
                if record.is_optional:
                    fees_struc = (
                        self.env["xe.fees.structure"]
                        .sudo()
                        .search(
                            [
                                ("is_optional", "=", self.is_optional),
                                ("company_id", "=", self.env.user.company_id.id),
                            ]
                        )
                    )
                    for fees in fees_struc:
                        for fees_line in fees.fee_details_ids:
                            if (
                                fees_line.fee_type_id.fee_type
                                in self.optional_fee_ids.mapped("fee_type")
                                and fees_line.term_id.id == record.term_id.id
                            ):
                                inv_line_vals = {
                                    "fee_type_id": fees_line.fee_type_id.id,
                                    "term_id": fees_line.term_id.id,
                                    "amount": fees_line.amount,
                                    "invoice_date": fees_line.invoice_date,
                                    "due_date": fees_line.due_date,
                                    "schedule_date": fees_line.schedule_date,
                                    "fee_structure_id": fees_struc.id,
                                    "receipt_name_id": fees_line.receipt_name_id.id,
                                    "fees_detail_id": fees_struc.id,
                                    "optional_fee": True,
                                }
                                invoice_line_ids.append([0, 0, inv_line_vals])

                # Show Boarding line product
                if record.is_boarding:
                    fees_struct_rec = (
                        self.env["xe.fees.structure"]
                        .sudo()
                        .search(
                            [
                                ("fee_structu_type", "=", "boarding"),
                                ("course_id", "in", self.course_id.id),
                            ]
                        )
                    )
                    if fees_struct_rec:
                        fee_details_line = (
                            self.env["xe.fees.details"]
                            .sudo()
                            .search(
                                [
                                    ("fee_structure_id", "=", fees_struct_rec.id),
                                    ("term_id", "=", record.term_id.id),
                                ]
                            )
                        )
                        for line in fee_details_line:
                            inv_line_vals = {
                                "fee_type_id": line.fee_type_id.id,
                                "term_id": line.term_id.id,
                                "amount": line.amount,
                                "invoice_date": line.invoice_date,
                                "due_date": line.due_date,
                                "schedule_date": line.schedule_date,
                                "fee_structure_id": fees_struct_rec.id,
                                "receipt_name_id": line.receipt_name_id.id,
                                "fees_detail_id": line.id,
                                "boarding_fee": True,
                            }
                            invoice_line_ids.append([0, 0, inv_line_vals])

                if invoice_line_ids:
                    record.fee_details_ids = False
                    record.fee_details_ids = invoice_line_ids

    def generate_fun(self):
        fees = (
            self.env["xe.fees.structure"]
            .sudo()
            .search(
                [
                    ("course_id", "in", self.course_id.id),
                    ("academic_year_id", "=", self.current_academic_year_id.id),
                ],
                limit=1,
            )
        )
        student_rec = self.student_id
        fees.with_context(
            student_rec=student_rec, academic_fee_wizard=True, wizard_obj=self
        ).generate()
        # Transport Invoice Generation Admission
        if self.is_transport:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("is_transport_fees", "=", self.is_transport),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ]
                )
            )
            student_rec = self.student_id
            student_rec.write(
                {
                    "is_transport": self.is_transport,
                    "fees_to_zone_id": self.fees_to_zone_id.id,
                }
            )
            fee_line_wizard = (
                self.env["xe.fees.details"]
                .sudo()
                .search(
                    [
                        ("fee_type_id", "=", self.fees_to_zone_id.id),
                        (
                            "fee_structure_id.academic_year_id",
                            "=",
                            self.current_academic_year_id.id,
                        ),
                    ]
                )
            )
            fees.with_context(
                student_rec=student_rec,
                fee_line_wizard=fee_line_wizard,
                wizard_obj=self,
            ).generate_transport()

            inv_list = []
            fee_lines = self.env["xe.fees.details"].search(
                [
                    ("fee_type_id", "=", self.fees_to_zone_id.id),
                    (
                        "fee_structure_id.academic_year_id",
                        "=",
                        self.current_academic_year_id.id,
                    ),
                ]
            )
            for fee in student_rec.fee_line_details_ids:
                fee.sudo().unlink()
            for i in fee_lines:
                inv_list.append(
                    [
                        0,
                        0,
                        {
                            "fee_type_id": i.fee_type.id,
                            "term_id": i.term_id.id,
                            "invoice_date": i.invoice_date,
                            "due_date": i.due_date,
                            "schedule_date": i.schedule_date,
                            "amount": i.amount,
                            "student_id": student_rec.id,
                        },
                    ]
                )
            account_move_rec = self.env["account.move"].search(
                [("partner_id", "=", student_rec.partner_id.id)]
            )
            student_rec.write(
                {
                    "fee_line_details_ids": inv_list,
                    "invoice_ids": [(6, 0, account_move_rec.ids)],
                }
            )
        # Activity Invoice Generation Admission form
        if self.is_activity:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("is_activity", "=", self.is_activity),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ]
                )
            )
            student_rec = self.student_id
            student_rec.write(
                {
                    "is_activity": self.is_activity,
                    "activity_fee_ids": self.activity_fee_ids.ids,
                }
            )
            # student_rec.write({'is_activity': True})
            fees.with_context(
                student_rec=student_rec, activity_fee_wizard=True, wizard_obj=self
            ).generate_activity()
            account_move_rec = self.env["account.move"].search(
                [("partner_id", "=", student_rec.partner_id.id)]
            )
            student_rec.write({"invoice_ids": [(6, 0, account_move_rec.ids)]})

        # Boarding Invoice Generation Admission form
        if self.is_boarding:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("fee_structu_type", "=", "boarding"),
                        ("course_id", "in", self.course_id.id),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ]
                )
            )
            student_rec = self.student_id
            student_rec.write({"is_boarding": self.is_boarding})
            fees.with_context(
                student_rec=student_rec, boarding_fee_wizard=True, wizard_obj=self
            ).generate_boarding()
            account_move_rec = self.env["account.move"].search(
                [("partner_id", "=", student_rec.partner_id.id)]
            )
            student_rec.write({"invoice_ids": [(6, 0, account_move_rec.ids)]})
        applc_id = (
            self.env["xe.application"].sudo().search([("id", "=", self.application_id)])
        )
        applc_id.state = "enrolled"

    def generate_new(self):
        student = self.student_id
        partner_id = student.partner_id
        terms = self.fee_details_ids.mapped("term_id")
        invoice_dates = self.fee_details_ids.mapped("invoice_date")
        check_term = all(x == terms[0] for x in terms)
        check_date = all(x == invoice_dates[0] for x in invoice_dates)
        is_transport = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_fees_management.is_transport")
        )
        is_activity = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_fees_management.is_activity")
        )
        # .get_param("xenesis_school_base.is_activity")
        is_boarding = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_fees_management.is_boarding")
        )
        is_optional = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_fees_management.is_optional")
        )
        move_obj = (
            self.env["account.move"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", partner_id.id),
                    ("is_application_invoice", "=", True),
                    ("fee_structu_type", "in", ["academic"]),
                ],
                limit=1,
            )
        )
        invoice_line_vals = []
        create_new_invoice = False
        inv_type = "out_invoice"
        reference = str(student.roll_number)
        move_vals = {
            "partner_id": partner_id.id,
            "move_type": inv_type,
            "ref": reference,
            "roll_number": student.roll_number,
            "course_id": self.course_id.id,
            "class_room_id": self.classroom_id.id,
            "terms": self.term_id.name,
        }
        inv_ids = []
        create_academic_fee = False
        create_activity_fee = False
        create_transport_fee = False
        create_boarding_fee = False
        create_optional_fee = False
        activity_inv_ids = []
        academic_inv_ids = []
        transport_inv_ids = []
        boarding_inv_ids = []
        optional_inv_ids = []
        is_add_discount_seperate = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_admission_management.is_add_discount_seperate")
        )
        disc_product_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_admission_management.discount_product_id")
        )
        disc_account_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_admission_management.discount_account_id")
        )
        product_obj = self.env["product.product"].search([("id", "=", disc_product_id)])
        discount_vals = {}
        for line in self.fee_details_ids:
            discount_vals2 = {}
            create_new_invoice = False
            account_id = False
            product_temp = (
                self.env["product.template"]
                .sudo()
                .search([("id", "=", line.fee_type_id.product_id.id)], limit=1)
            )
            product = product_temp.product_variant_id
            if not move_obj or (
                move_obj
                and product.id not in move_obj.invoice_line_ids.mapped("product_id").ids
            ):
                if product.property_account_income_id:
                    account_id = product.property_account_income_id.id
                if not account_id:
                    account_id = product.categ_id.property_account_income_categ_id.id
                if not account_id:
                    raise UserError(
                        _('There is no income account defined for this product: "%s"')
                        % product.name
                    )
                line_vals = {
                    "name": line.receipt_name_id.name or product.name,
                    "account_id": account_id,
                    "price_unit": line.amount,
                    "quantity": 1.0,
                    "product_id": product.id,
                    "receipt_name_id": line.receipt_name_id.id,
                }
                if line.academic_fee:
                    create_academic_fee = "new"
                    move_vals["invoice_date"] = line.invoice_date
                    invoice_line_vals.append((0, 0, line_vals))
                if line.activity_fee:
                    if not is_activity:
                        # if check_term and check_date:
                        create_activity_fee = "update"
                        invoice_line_vals.append((0, 0, line_vals))
                        # else:
                        #     create_activity_fee = "new"
                        #     create_new_invoice = True
                    else:
                        create_activity_fee = "new"
                        create_new_invoice = True
                if line.optional_fee:
                    if not is_optional:
                        # if check_term and check_date:
                        create_optional_fee = "update"
                        invoice_line_vals.append((0, 0, line_vals))
                        # else:
                        #     create_optional_fee = "new"
                        #     create_new_invoice = True
                    else:
                        create_optional_fee = "new"
                        create_new_invoice = True
                if line.transport_fee:
                    if not is_transport:
                        # if check_term and check_date:
                        invoice_line_vals.append((0, 0, line_vals))
                        create_transport_fee = "update"
                        # else:
                        # create_transport_fee = "new"
                        # create_new_invoice = True
                    else:
                        create_transport_fee = "new"
                        create_new_invoice = True
                if line.boarding_fee:
                    if is_boarding:
                        if check_term and check_date:
                            create_boarding_fee = "update"
                            invoice_line_vals.append((0, 0, line_vals))
                        else:
                            create_boarding_fee = "new"
                            create_new_invoice = True
                    else:
                        create_boarding_fee = "new"
                        create_new_invoice = True
                if line.discount or line.fixed_discount:
                    if is_add_discount_seperate:
                        discount_amt = 0
                        if line.discount:
                            discount_amt += (line.amount * line.discount) / 100
                        if line.fixed_discount:
                            discount_amt += line.fixed_discount
                        if discount_amt:
                            discount_amt = discount_amt * -1
                        if create_new_invoice:
                            discount_vals2 = {
                                "name": line.receipt_name_id.name or product_obj.name,
                                "account_id": int(disc_account_id),
                                "price_unit": discount_amt,
                                "quantity": 1.0,
                                "product_id": product_obj.id,
                            }
                        else:
                            if not discount_vals:
                                discount_vals = {
                                    "name": line.receipt_name_id.name
                                    or product_obj.name,
                                    "account_id": int(disc_account_id),
                                    "price_unit": discount_amt,
                                    "quantity": 1.0,
                                    "product_id": product_obj.id,
                                }
                            else:
                                discount_vals["price_unit"] += discount_amt
                    else:
                        if line.discount:
                            line_vals["discount"] = line.discount
                        if line.fixed_discount:
                            line_vals["discount_fixed"] = line.fixed_discount
                if create_new_invoice:
                    move_vals["invoice_date"] = line.invoice_date
                    move_vals["invoice_line_ids"] = [(0, 0, line_vals)]
                    if discount_vals2:
                        move_vals["invoice_line_ids"].append((0, 0, discount_vals2))
                    move = self.env["account.move"].sudo().create(move_vals)
                    if create_academic_fee and create_academic_fee == "new":
                        create_academic_fee = False
                        academic_inv_ids.append(move.id)
                    if create_activity_fee and create_activity_fee == "new":
                        create_activity_fee = False
                        academic_inv_ids.append(move.id)
                    if create_optional_fee and create_optional_fee == "new":
                        create_optional_fee = False
                        academic_inv_ids.append(move.id)
                    if (
                        create_transport_fee
                        and create_transport_fee == "new"
                        and is_transport
                    ):
                        create_transport_fee = False
                        academic_inv_ids.append(move.id)
                    if create_boarding_fee and create_boarding_fee == "new":
                        create_boarding_fee = False
                        academic_inv_ids.append(move.id)
                    inv_ids.append(move.id)
        if invoice_line_vals:
            if discount_vals:
                invoice_line_vals.append((0, 0, discount_vals))
            if move_obj and move_obj.invoice_date == move_vals["invoice_date"]:
                move_obj.write(
                    {
                        "invoice_line_ids": invoice_line_vals,
                    }
                )
                academic = transport = optional = activity = boarding = False
                if line.academic_fee:
                    academic = True
                    fee_struct_type = "academic"
                if line.is_optional:
                    transport = True
                    fee_struct_type = "optional"
                if line.transport_fee:
                    optional = True
                    fee_struct_type = "transport"
                if line.activity_fee:
                    activity = True
                    fee_struct_type = "activity"
                if line.boarding_fee:
                    boarding = True
                move.write(
                    {
                        "is_academic": academic,
                        "is_optional": transport,
                        "is_transport_fees": optional,
                        "is_activity": activity,
                        "is_boarding": boarding,
                        # "fee_structu_type": fee_struct_type,
                    }
                )
                inv_ids.append(move_obj.id)
                if create_academic_fee and create_academic_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_activity_fee and create_activity_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_optional_fee and create_optional_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_transport_fee and create_transport_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_boarding_fee and create_boarding_fee == "update":
                    academic_inv_ids.append(move.id)
            else:
                move_vals["invoice_line_ids"] = invoice_line_vals
                move = self.env["account.move"].sudo().create(move_vals)
                academic = transport = optional = activity = boarding = False
                if line.academic_fee:
                    academic = True
                    fee_struct_type = "academic"
                if line.is_optional:
                    transport = True
                    fee_struct_type = "optional"
                if line.transport_fee:
                    optional = True
                    fee_struct_type = "transport"
                if line.activity_fee:
                    activity = True
                    fee_struct_type = "activity"
                if line.boarding_fee:
                    boarding = True
                move.write(
                    {
                        "is_academic": academic,
                        "is_optional": transport,
                        "is_transport_fees": optional,
                        "is_activity": activity,
                        "is_boarding": boarding,
                        # "fee_structu_type": fee_struct_type,
                    }
                )

                inv_ids.append(move.id)
                # Invoice ID map with fees structure
                if create_academic_fee and create_academic_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_activity_fee and create_activity_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_optional_fee and create_optional_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_transport_fee and create_transport_fee == "update":
                    academic_inv_ids.append(move.id)
                if create_boarding_fee and create_boarding_fee == "update":
                    academic_inv_ids.append(move.id)
                account_invoices = (
                    self.env["account.move"].sudo().search([("id", "in", inv_ids)])
                )
                account_invoices.write(
                    {"is_application_invoice": True, "fee_structu_type": "academic"}
                )
        if transport_inv_ids:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("course_id", "in", self.course_id.ids),
                        ("is_transport_fees", "=", self.is_transport),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ],
                    limit=1,
                )
            )
            fees.write({"invoice_ids": [(6, 0, transport_inv_ids)]})
        if academic_inv_ids:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("course_id", "in", self.course_id.ids),
                        ("fee_structu_type", "=", "academic"),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ],
                    limit=1,
                )
            )
            fees.write({"invoice_ids": [(6, 0, academic_inv_ids)]})
        if boarding_inv_ids:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("course_id", "in", self.course_id.ids),
                        ("fee_structu_type", "=", "boarding"),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ],
                    limit=1,
                )
            )
            fees.write({"invoice_ids": [(6, 0, boarding_inv_ids)]})
        if activity_inv_ids:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("course_id", "in", self.course_ids.id),
                        ("is_activity", "=", self.is_activity),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ],
                    limit=1,
                )
            )
            fees.write({"invoice_ids": [(6, 0, boarding_inv_ids)]})
        if optional_inv_ids:
            fees = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("course_id", "in", self.course_ids.id),
                        ("is_optional", "=", self.is_optional),
                        ("academic_year_id", "=", self.current_academic_year_id.id),
                    ],
                    limit=1,
                )
            )
            fees.write({"invoice_ids": [(6, 0, optional_inv_ids)]})
        applc_id = (
            self.env["xe.application"].sudo().search([("id", "=", self.application_id)])
        )
        applc_id.state = "enrolled"
        if not applc_id.admission_number:
            applc_id.admission_number = student.roll_number

        student.write(
            {
                "is_transport": self.is_transport,
                "is_activity": self.is_activity,
                "is_boarding": self.is_boarding,
                "is_optional": self.is_optional,
                "fees_to_zone_id": self.fees_to_zone_id.id,
                "activity_fee_ids": self.activity_fee_ids.ids,
                "optional_fee_ids": self.optional_fee_ids.ids,
            }
        )
        return True


class AdmissionFeeDetailsWizard(models.TransientModel):
    _name = "admn.fees.details.wizard"

    fee_structure_id = fields.Many2one("xe.fees.structure", string="Fee Structure Line")
    fee_structure_wiz_id = fields.Many2one(
        "admission.fee.wizard", string="Fee Structure Line"
    )
    is_activity = fields.Boolean(
        related="fee_structure_wiz_id.is_activity", string="Is Activity Fees"
    )
    is_transport_fees = fields.Boolean(
        related="fee_structure_wiz_id.is_transport", string="Is Transport Fees"
    )
    is_boarding = fields.Boolean(
        related="fee_structure_wiz_id.is_boarding", string="Is Boarding Fees"
    )
    is_optional = fields.Boolean(
        related="fee_structure_wiz_id.is_optional", string="Is Optional Fees"
    )
    fee_type_id = fields.Many2one("xe.fees.type")  # , required=True
    academic_year_id = fields.Many2one("xe.academic.year")
    term_id = fields.Many2one("xe.academic.terms", string="Terms")
    due_days = fields.Integer(related="fee_structure_wiz_id.due_days", store=True)
    invoice_date = fields.Date()
    due_date = fields.Date(compute="_compute_due_date", store=True)
    schedule_date = fields.Date()
    currency_id = fields.Many2one("res.currency")
    receipt_name_id = fields.Many2one("fee.receipt")
    amount = fields.Monetary(currency_field="currency_id")
    discount = fields.Float("Disc%")
    fixed_discount = fields.Float()
    student_id = fields.Many2one("xe.student", string="Student ID")
    parent_state = fields.Selection(
        [("draft", "Draft"), ("invoice", "Invoice Created")],
        default="draft",
        string="Status",
        tracking=True,
    )
    fees_detail_id = fields.Many2one("xe.fees.details", string="Fees Detail")
    activity_fee = fields.Boolean()
    academic_fee = fields.Boolean()
    boarding_fee = fields.Boolean()
    transport_fee = fields.Boolean()
    optional_fee = fields.Boolean()
    discounted_amt = fields.Float("Total Amount", compute="_compute_set_total_amount")

    @api.depends("amount", "discount", "fixed_discount")
    def _compute_set_total_amount(self):
        for line in self:
            discounted_amt = 0
            if line.amount and line.discount:
                discounted_amt = line.amount - (line.amount * line.discount / 100)
            if line.amount and line.fixed_discount:
                discounted_amt = line.amount - line.fixed_discount
            line.discounted_amt = discounted_amt

    @api.depends("due_days")
    def _compute_due_date(self):
        for i in self:
            current_date = datetime.datetime.now().date()
            self.due_date = current_date + datetime.timedelta(days=int(i.due_days))
