from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class Contract(models.Model):
    # _inherit = "hr.contract"
    _inherit = "hr.version"
    @api.onchange("employee_id")
    def _set_yearly_wage(self):
        for rec in self:
            if rec.employee_id.emp_salary_grade_id and rec.employee_id.salary_band:
                if rec.employee_id.salary_band == "low":
                    rec.yearly_wage = rec.employee_id.emp_salary_grade_id.low_band
                elif rec.employee_id.salary_band == "mid":
                    rec.yearly_wage = rec.employee_id.emp_salary_grade_id.mid_band
                elif rec.employee_id.salary_band == "high":
                    rec.yearly_wage = rec.employee_id.emp_salary_grade_id.high_band

    def get_all_emails(self):
        users = self.env["res.users"].search([])
        emails = ""

        for user in users:
            if user.has_group("hr_payroll.group_hr_payroll_manager") or user.has_group(
                "hr.group_hr_manager"
            ):
                if not emails:
                    emails = emails + user.login
                else:
                    emails = emails + "," + user.login
        return emails

    @api.model
    def _expiry_contract_notification(self):
        contracts = self.search(
            [("employee_id", "!=", False), ("contract_date_end", "!=", False)]
        ).filtered(lambda version: version._is_in_contract())
        from datetime import date

        today = date.today()
        expiry_date = fields.Date.from_string(today) + relativedelta(days=15)
        for contract in contracts:
            emails = self.get_all_emails()
            if contract.date_end <= expiry_date:
                emp_email = contract.employee_id.work_email or ""
                if emails:
                    emails = emails + "," + emp_email
                else:
                    emails = emp_email
                contract.emails = emails
                template = self.env.ref("xe_kenya_hr_payroll.email_contract_expiry")
                template.send_mail(contract.id, force_send=True)

    emp_belonging_id = fields.Many2one(
        "hr.employee.belonging", related="employee_id.emp_belonging_id"
    )
    emp_type = fields.Selection(related="employee_id.emp_type")
    employee_no = fields.Char("Employee Number", related="employee_id.employee_no")
    yearly_wage = fields.Monetary(string="Wage")
    contract_type = fields.Selection(related="employee_id.contract_type")
    emails = fields.Char()
    nssf_amount = fields.Monetary(
        string="NSSF Amount",
        help="National Social Security Fund Amount",
        default=1080.0,
    )
    sacco_contribution = fields.Monetary(string="KIMISITU SACCO Contribution")
    insurance_premium = fields.Monetary()
    pension_contribution = fields.Monetary(string="Voluntary Pension Contribution")
    monthly_personal_relief = fields.Monetary()
    medical_deduction = fields.Monetary()
    gratuity = fields.Monetary(string="Gratuity Amount")
    transport_allowance = fields.Monetary()
    extra_class_allowance = fields.Monetary(
        string="Extra Classes/Evening Classes Allowance"
    )
    monthly_tax_allowance = fields.Monetary()
    welfare_contribution = fields.Monetary()
    monthly_insurance_relief = fields.Monetary(
        string="Insurance Relief"
    )
    other_earnings = fields.Monetary()
    schoolfees_deduction = fields.Monetary(string="School Fees")
    monthly_medical_insurance = fields.Monetary(string="Insurance")
    house_bonus = fields.Monetary()
    food_allowance = fields.Monetary()
    payroll_type = fields.Selection(
        [("12_month", "12 Months"), ("13_month", "13 Months")], default="12_month"
    )
    finnlem_sacco_contribution = fields.Monetary(string="FINNLEMM SACCO Contribution")
    parking_fee = fields.Monetary()
    other_deductions = fields.Monetary()
    is_activity_rate = fields.Boolean("Activate Activity Rate")
    activity_rate = fields.Float()
    consolidated_benefits = fields.Float("Consolidated Benefits Support")
    school_fees_benefits = fields.Monetary()
    helb_deduction = fields.Monetary(string="HELB Deduction", tracking=True)
    is_pension = fields.Boolean(string="Pension", tracking=True)
    bonus = fields.Monetary(tracking=True)

    @api.constrains("pension_contribution")
    def validate_pension_contribution(self):
        for record in self:
            if record.pension_contribution > 19800:
                raise ValidationError(
                    _("Voluntary pension contribution cannot exceed 19800")
                )

    @api.onchange("payroll_type", "yearly_wage")
    def _set_wage(self):
        for contract in self:
            if contract.payroll_type:
                if contract.payroll_type == "12_month":
                    contract.wage = contract.yearly_wage / 12
                else:
                    contract.wage = contract.yearly_wage / 13
