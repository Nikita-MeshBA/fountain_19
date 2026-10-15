# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    mpesa_paybill = fields.Text(related="company_id.mpesa_paybill", readonly=False)
    account = fields.Char(related="company_id.account", readonly=False)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    current_academic_year_id = fields.Many2one(
        "xe.academic.year",
        related="company_id.current_academic_year_id",
        readonly=False,
    )
    class_admission_no_automatic = fields.Boolean(
        string="Generate Admission Number Automatically Based on Class",
        config_parameter="xenesis_school_base.class_admission_no_automatic",
    )
    is_add_discount_seperate = fields.Boolean("Add Discount Line in Invoice Lines")
    discount_product_id = fields.Many2one(
        "product.product",
        config_parameter="xenesis_school_base.discount_product_id",
    )
    discount_account_id = fields.Many2one(
        "account.account",
        config_parameter="xenesis_school_base.discount_account_id",
    )
    is_schedule_interview = fields.Boolean("Schedule Interview")
    balance_on_invoice = fields.Boolean()
    parent_generic_password = fields.Char(
        string='Parent Generic Password',
        config_parameter='xenesis_school_base.parent_generic_password'
    )

    def generate_academic_year(self):
        current_date = fields.date.today()
        academic_record = (
            self.env["xe.academic.year"]
            .sudo()
            .search(
                [("start_date", "<=", current_date), ("end_date", ">=", current_date)],
                limit=1,
            )
        )
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        if config_param:
            config_param.value = academic_record.id
        else:
            self.env["ir.config_parameter"].sudo().create(
                {
                    "key": "xenesis_school_base.current_academic_year_id",
                    "value": academic_record.id,
                }
            )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        class_admission_no_automatic = params.get_param(
            "xenesis_school_base.class_admission_no_automatic"
        )
        is_add_discount_seperate = params.get_param(
            "xenesis_school_base.is_add_discount_seperate", default=False
        )
        is_schedule_interview = params.get_param(
            "xenesis_school_base.is_schedule_interview", default=False
        )
        balance_on_invoice = params.get_param(
            "xenesis_school_base.balance_on_invoice", default=False
        )

        res.update(
            class_admission_no_automatic=class_admission_no_automatic,
            is_add_discount_seperate=is_add_discount_seperate,
            is_schedule_interview=is_schedule_interview,
            balance_on_invoice=balance_on_invoice,
        )

        # Update existing records course table is_sequence value based on setting
        # course_rec = self.env["xe.course"].sudo().search([])
        # for c in course_rec:
        #     if class_admission_no_automatic:
        #         admission_seq = (
        #             self.env["ir.sequence"]
        #             .sudo()
        #             .search([("code", "=", "xe.admission.enquiry")], limit=1)
        #         )
        #         c.write(
        #             {
        #                 "is_sequence": class_admission_no_automatic,
        #                 "classroom_seq_id": admission_seq.id,
        #             }
        #         )
        #     else:
        #         c.write({"is_sequence": class_admission_no_automatic})

        if self.company_id.current_academic_year_id:
            student_rec = (
                self.env["xe.student"]
                .sudo()
                .search([("company_id", "=", self.env.company.id)])
            )
            for s in student_rec:
                s.current_academic_year_id = self.company_id.current_academic_year_id.id
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "xenesis_school_base.current_academic_year_id", self.current_academic_year_id.id
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xenesis_school_base.class_admission_no_automatic",
            self.class_admission_no_automatic,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xenesis_school_base.is_schedule_interview",
            self.is_schedule_interview,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xenesis_school_base.is_add_discount_seperate",
            self.is_add_discount_seperate,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xenesis_school_base.discount_product_id",
            self.discount_product_id.id,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xenesis_school_base.discount_account_id",
            self.discount_account_id.id,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "xenesis_school_base.balance_on_invoice",
            self.balance_on_invoice,
        )
