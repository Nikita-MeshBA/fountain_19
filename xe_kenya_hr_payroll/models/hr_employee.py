import random
import calendar
import logging
import random
import string

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    @api.constrains("debit_account_id")
    def _check_account(self):
        for line in self:
            if line.debit_account_id and not line.debit_account_id.isdigit():
                raise UserError(_("Invalid Debit Account!!! Please check"))

    def write(self, values):
        if "emp_salary_grade_id" in values or "salary_band" in values:
            emp_salary_grade_id = (
                self.emp_salary_grade_id and self.emp_salary_grade_id.id or False
            )
            salary_band = self.salary_band
            if "emp_salary_grade_id" in values:
                emp_salary_grade_id = values["emp_salary_grade_id"]
            if "salary_band" in values:
                salary_band = values["salary_band"]
            emp_salary_grade_obj = self.env["hr.salary.grade"].search(
                [("id", "=", emp_salary_grade_id)]
            )
            yearly_wage = 0
            if salary_band == "low":
                yearly_wage = emp_salary_grade_obj.low_band
            elif salary_band == "mid":
                yearly_wage = emp_salary_grade_obj.mid_band
            elif salary_band == "high":
                yearly_wage = emp_salary_grade_obj.high_band

            # contracts are hr.version records since Odoo 19
            running_contract_obj = self.version_id.filtered(
                lambda version: version._is_in_contract()
            )
            running_contract_id = (
                running_contract_obj and running_contract_obj.id or False
            )

            wage = 0
            if running_contract_id:
                payroll_type = running_contract_obj.payroll_type
                if payroll_type and payroll_type == "12_month":
                    wage = yearly_wage / 12
                elif payroll_type and payroll_type == "13_month":
                    wage = yearly_wage / 13
                running_contract_obj.write({"yearly_wage": yearly_wage, "wage": wage})
        result = super(Employee, self).write(values)
        return result

    def get_all_emails(self):
        users = self.env["res.users"].search([])
        emails = ""
        for user in users:
            if user.has_group("hr.group_hr_manager"):
                if not emails:
                    emails = emails + user.login
                else:
                    emails = emails + "," + user.login
        return emails

    @api.model
    def _expiry_visa_notification(self):
        employees = self.search([("visa_expire", "!=", False)])
        from datetime import date

        today = date.today()
        expiry_date = fields.Date.from_string(today) + relativedelta(days=15)
        for employee in employees:
            emails = self.get_all_emails()

            if employee.visa_expire <= expiry_date:
                emp_email = employee.work_email or ""
                if emails:
                    emails = emails + "," + emp_email
                else:
                    emails = emp_email

                employee.emails = emails
                # l10_kenya_hr_payroll module not available
                template = self.env.ref("l10_kenya_hr_payroll.email_visa_expiry")
                template.send_mail(employee.id, force_send=True)

    def employee_form_server_action(self):
        search_view_id = self.env.ref("hr.view_employee_filter")
        view_mode = "kanban"
        if self.env.user.has_group("hr.group_hr_user"):
            view_mode = "kanban,list,form,activity"

        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.employee",
            "name": "Employees",
            "view_mode": view_mode,
            "search_view_id": search_view_id and search_view_id.id,
            "target": "current",
        }

    pin_no = fields.Char(string="PIN No", help="Personal Identification Number")
    nssf_no = fields.Char(string="NSSF No", help="National Social Security Fund")
    nhif_no = fields.Char(string="NHIF No", help="National Hospital Insurance Fund")
    # old field
    bic = fields.Many2one("res.bank", string="Bank")
    # new field
    bic_id = fields.Many2one("res.bank", string="Bank")
    debit_account_id = fields.Char("Account Number")
    branch_code = fields.Char()
    qualification = fields.Char()
    tsc_no = fields.Char(string="TSC No", help="Teacher's Service Commission")
    emp_type = fields.Selection(
        [("international", "Non Kenyan"), ("kenyan", "Kenyan")],
        string="Employee Type",
        default="kenyan",
    )
    # old field
    emp_belonging = fields.Many2one("hr.employee.belonging", "Employee Belonging")
    # new field
    emp_belonging_id = fields.Many2one("hr.employee.belonging", "Employee Belonging")
    emp_salary_grade_id = fields.Many2one("hr.salary.grade", string="Employee Category")
    salary_band = fields.Selection(
        [("low", "Minimum"), ("mid", "Intermediate"), ("high", "Maximum")],
        default="low",
    )
    employee_no = fields.Char()
    dependency_ids = fields.One2many(
        "hr.dependency", "employee_id", "Dependency Details"
    )
    nita_no = fields.Char(string="NITA No")
    contract_type = fields.Selection(
        [("regular", "Regular"), ("casual", "Casual"), ("intern", "Intern")],
        default="regular",
    )
    emails = fields.Char()
    identification_id1 = fields.Char(
        related="identification_id", string="Identification No"
    )
    insurance_scheme_ids = fields.Many2many(
        "hr.insurance.scheme",
        "hr_insurance_scheme_rel",
        "employee_id",
        "insurance_id",
        string="Insurance Schemes",
        copy=False,
    )
    life_insurance_ids = fields.One2many(
        "hr.life.insurance", "employee_id", string="Life Insurance", copy=False
    )
    helb_ids = fields.One2many(
        "hr.helb", "employee_id", string="Higher Education Loan Board", copy=False
    )
    longterm_advance_ids = fields.One2many(
        "hr.long.term.advance", "employee_id", string="Long Term Advance", copy=False
    )
    joining_date = fields.Date()
    probation_end_date = fields.Date()
    gratuity_date = fields.Date()
    residential_status_id = fields.Many2one("residential.status", "Residential Status")
    type_of_employee_id = fields.Many2one("type.of.employee", "Type of Employee")
    swift_code = fields.Char()
    kra_pin = fields.Char(string="KRA Pin", help="Kenya Revenue Authority")
    joined_date = fields.Date(string="Joining Date")
    identification_id = fields.Char(string="Identification No", copy=False)
    registration_number = fields.Char(
        "Registration Number of the Employee", groups="hr.group_hr_user", copy=False
    )
    employee_no = fields.Char()

    _unique_registration_number = models.Constraint(
        "UNIQUE(registration_number, company_id)",
        "No duplication of registration numbers is allowed",
    )

    @api.constrains("joining_date", "probation_end_date")
    def check_dates(self):
        for record in self:
            if record.joining_date and record.probation_end_date:
                joining_date = fields.Date.from_string(record.joining_date)
                probation_end_date = fields.Date.from_string(record.probation_end_date)
                if joining_date > probation_end_date:
                    raise ValidationError(
                        _(
                            "Probation End Date cannot be set \
                            before Joining Date."
                        )
                    )

    @api.onchange("probation_end_date")
    def onchange_probation_end_date(self):
        if self.probation_end_date and self.company_id.gratuity_period:
            self.gratuity_date = self.probation_end_date + relativedelta(
                months=self.company_id.gratuity_period
            )

    @api.onchange("bic_id")
    def onchange_probation_end_date(self):
        if self.bic_id and self.bic_id.id:
            self.swift_code = self.bic_id and self.bic_id.swift_code or ""

    @api.model
    def _generate_identification_id(self):
        """Generate a random employee identification number"""
        company = self.env.user.company_id

        steps = 0
        for _retry in range(50):
            employee_id = False
            if company.employee_id_gen_method == "sequence":
                if not company.employee_sequence_id:
                    _logger.warning("No sequence configured for employee ID generation")
                    return employee_id
                employee_id = company.employee_sequence_id.next_by_id()
            elif company.employee_id_gen_method == "random":
                employee_id_random_digits = company.employee_id_random_digits
                rnd = random.SystemRandom()
                employee_id = "".join(
                    rnd.choice(string.digits) for x in range(employee_id_random_digits)
                )

            if self.search_count([("identification_id", "=", employee_id)]):
                steps += 1
                continue
            return employee_id
        raise UserError(
            _("Unable to generate unique Employee ID in %d steps.") % (steps,)
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("registration_number"):
                vals["registration_number"] = self._generate_identification_id()
        return super(Employee, self).create(vals_list)


class EmployeeDats(models.Model):
    _name = "employee.data"
    _description = "Employee Data"

    employee_name = fields.Char("Name", readonly=True)
    employee_no = fields.Char(string="Employee Number", readonly=True)
    working_days = fields.Char(readonly=True)
    entitle_days = fields.Integer(default=0, string="Entitled Days")
    employee_id = fields.Char("Employee ID")
    food_allowance = fields.Float()
    transport_allowance = fields.Float()
    entitle_employee_id = fields.Many2one("entitle.employee.days")


class EmployeeDependencies(models.Model):
    _name = "hr.dependency"
    _description = "HR Dependency"

    name = fields.Char()
    relation = fields.Char()
    contact_no = fields.Char()
    dob = fields.Date("DOB")
    employee_id = fields.Many2one("hr.employee", "Employee")


class EntitleEmployeeDays(models.Model):
    _name = "entitle.employee.days"
    _description = "Entitle Employee Days"
    _rec_name = "display_name"

    def _get_default_end_date(self):
        last_day = calendar.monthrange(
            fields.Date.today().year, fields.Date.today().month
        )[1]
        return fields.Date.today().replace(day=last_day)

    display_name = fields.Char("Name", default="/")
    name = fields.Selection(
        [
            ("january", "January"),
            ("feb", "Febury"),
            ("march", "March"),
            ("april", "Aprile"),
            ("may", "May"),
            ("june", "June"),
            ("july", "July"),
            ("august", "August"),
            ("september", "September"),
            ("october", "October"),
            ("november", "November"),
            ("december", "December"),
        ],
        default="december",
    )
    start_date = fields.Date(default=fields.Date.today().replace(day=1))
    end_date = fields.Date(default=_get_default_end_date)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")], default="draft"
    )

    @api.onchange("start_date", "end_date")
    def _set_name(self):
        for line in self:
            if line.start_date and line.end_date:
                line.display_name = (
                    "Entitled Employee Day's of "
                    + self.start_date.strftime("%d %b %Y")
                    + " to "
                    + self.end_date.strftime("%d %b %Y")
                )

    @api.constrains("start_date", "end_date")
    def _check_duplicated_records(self):
        for rec in self:
            if rec.start_date > rec.end_date:
                raise UserError(_("The Start Date must be less than End Date"))
            records_count = self.env["entitle.employee.days"].search_count(
                [("start_date", ">=", rec.start_date), ("end_date", "<=", rec.end_date)]
            )
            if records_count > 1:
                raise UserError(
                    _(
                        "There is already a record within the same period.Please check!!!"
                    )
                )

    def _default_employee_id(self):
        employee_rec = self.env["hr.employee"].sudo().search([])
        working_days = (
            int(
                self.env["ir.config_parameter"].get_param(
                    "hr_msf_employee_sybyl.working_days"
                )
            )
            or 0
        )
        employee_list = []
        for i in employee_rec:
            dict_vals = {
                "employee_id": i.id,
                "employee_name": i.name,
                "employee_no": i.employee_no,
                "working_days": working_days,
                "entitle_days": 0,
                "entitle_employee_id": i.id,
            }
            employee_list.append([0, 0, dict_vals])
        return employee_list

    employee_data_ids = fields.One2many(
        "employee.data",
        "entitle_employee_id",
        default=lambda self: self._default_employee_id(),
    )

    def confirm(self):
        for i in self.employee_data_ids:
            contract_rec = (
                self.env["hr.employee"].sudo().browse(int(i.employee_id)).version_id
            )
            if contract_rec:
                if int(i.entitle_days) > 0:
                    transport_allowance = contract_rec.transport_allowance
                    food_allowance = contract_rec.food_allowance * int(i.entitle_days)
                else:
                    transport_allowance = 0
                    food_allowance = 0
                i.transport_allowance = transport_allowance
                i.food_allowance = food_allowance

        self.state = "confirmed"

    def set_to_draft(self):
        self.state = "draft"
