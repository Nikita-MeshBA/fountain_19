# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    gratuity_period = fields.Integer(
        related="company_id.gratuity_period", string="Gratuity Period"
    )
    nssf_no = fields.Char(
        string="NSSF No",
        help="National Social Security Fund",
        related="company_id.nssf_no",
    )
    nhif_no = fields.Char(
        string="NHIF No",
        help="National Hospital Insurance Fund",
        related="company_id.nhif_no",
    )
    helb_no = fields.Char(
        string="HELB No",
        help="Higher Education Loan Board",
        related="company_id.helb_no",
    )
    send_payslip_mail = fields.Boolean("Send Payslip By Email")
    nita_deduction_amt = fields.Monetary(string="NITA Amount")
    working_days = fields.Integer(
        string="Total Working Days",
    )
    employee_id_gen_method = fields.Selection(
        related="company_id.employee_id_gen_method",
        readonly=False,
        default=lambda self: self._default_id_gen_method(),
    )
    employee_id_random_digits = fields.Integer(
        related="company_id.employee_id_random_digits",
        readonly=False,
        default=lambda self: self._default_id_random_digits(),
    )
    employee_sequence_id = fields.Many2one(
        "ir.sequence",
        related="company_id.employee_sequence_id",
        readonly=False,
        default=lambda self: self._default_id_sequence(),
    )

    def _default_id_gen_method(self):
        gen_method = self.env.user.company_id.employee_id_gen_method
        if not gen_method:
            gen_method = self.env["res.company"].default_get(
                ["employee_id_gen_method"]
            )["employee_id_gen_method"]
        return gen_method

    def _default_id_random_digits(self):
        digits = self.env.user.company_id.employee_id_random_digits
        if not digits:
            digits = self.env["res.company"].default_get(["employee_id_random_digits"])[
                "employee_id_random_digits"
            ]
        return digits

    def _default_id_sequence(self):
        sequence = self.env.user.company_id.employee_sequence_id
        return sequence and sequence.id or False

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        working_days = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("working_days", default=False)
        )
        res.update(
            nita_deduction_amt=self.env["ir.config_parameter"]
            .sudo()
            .get_param("nita_deduction_amt"),
            working_days=working_days,
            send_payslip_mail=self.env["ir.config_parameter"]
            .sudo()
            .get_param("send_payslip_mail"),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "nita_deduction_amt", self.nita_deduction_amt
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "send_payslip_mail", self.send_payslip_mail
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "working_days", self.working_days
        )
