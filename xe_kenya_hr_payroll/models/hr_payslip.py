import math
import time
from datetime import datetime

import babel
import pytz
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, tools, _


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def send_email_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        for rec in active_ids:
            obj = self.browse(rec)
            obj.send_email()

    def send_email(self):
        template = self.env.ref("xe_kenya_hr_payroll.email_template_hr_payslip")
        email_from = self.env.user.company_id.email
        email_to = self.employee_id.work_email
        email_vals = {"email_from": email_from, "email_to": email_to}
        template.send_mail(self.id, email_values=email_vals, force_send=True)
        return True

    def _compute_get_payslip_mail(self):
        for line in self:
            payslip_mail = (
                self.env["ir.config_parameter"].sudo().get_param("send_payslip_mail")
            )
            line.is_send_payslip_mail = payslip_mail

    @api.depends("date_from", "date_to")
    def _compute_payslip_month(self):
        for slip in self:
            date_from = slip.date_from.strftime("%Y-%m-%d")
            ttyme = datetime.fromtimestamp(
                time.mktime(time.strptime(date_from, "%Y-%m-%d"))
            )
            locale = self.env.context.get("lang") or "en_US"
            month_y = str(
                babel.dates.format_date(date=ttyme, format="MMMM-y", locale=locale)
            )
            slip.payslip_month = month_y

    @api.depends("worked_days_line_ids.number_of_days")
    def _compute_worked_days(self):
        for payslip in self:
            payslip.sum_worked_days = sum(
                [line.number_of_days for line in payslip.worked_days_line_ids]
            )

    @api.depends("line_ids")
    def _compute_net_wage(self):
        line_ids = self.line_ids
        net_wage = 0
        for line in line_ids:
            if line.code == "NET":
                net_wage = line.amount
        self.net_wage = net_wage

    @api.depends("date_to")
    def _compute_get_last_month(self):
        for slip in self:
            slip.is_last_month = fields.Date.from_string(slip.date_to).month == 12

    def _compute_get_dec_basic(self):
        for slip in self:
            if slip.is_last_month and slip.employee_id and slip.date_to:
                contract = slip.contract_id
                if contract and contract.payroll_type == "13_month":
                    contract_date_start_object = datetime.strptime(
                        str(contract.date_start), "%Y-%m-%d"
                    )
                    slip_date_to_object = datetime.strptime(
                        str(slip.date_to), "%Y-%m-%d"
                    )
                    slip_year_start = datetime(slip_date_to_object.year, 1, 1)
                    if contract_date_start_object <= slip_year_start:
                        slip.dec_basic_salary = contract._get_contract_wage() / 1.15
                        slip.dec_hra = (
                            slip.dec_basic_salary
                            + (contract._get_contract_wage() / 1.15)
                        ) * 0.15
                    else:
                        slip_year_end = datetime(
                            slip_date_to_object.year, 12, 31
                        ).date()
                        diff_days = (
                            slip_year_end - contract_date_start_object.date()
                        ).days + 1
                        slip.dec_basic_salary = (
                            contract._get_contract_wage() / 1.15
                        ) * (diff_days / 365)
                        slip.dec_hra = (
                            (
                                (contract._get_contract_wage() / 1.15)
                                + slip.dec_basic_salary
                            )
                            * 0.15
                            * (diff_days / 365)
                        )
                else:
                    slip.dec_hra = 0
                    slip.dec_basic_salary = 0
            else:
                slip.dec_hra = 0
                slip.dec_basic_salary = 0

    sum_worked_days = fields.Float(compute="_compute_worked_days")
    net_wage = fields.Float(compute="_compute_net_wage", store=True)
    payslip_month = fields.Char(compute="_compute_payslip_month", store=True)
    is_january = fields.Boolean(
        compute="_compute_is_january", store=True, string="Is January?"
    )
    last_year_total_salary = fields.Float(store=True)
    work_perc = fields.Float(compute="_compute_get_work_percentage")
    is_send_payslip_mail = fields.Boolean(compute="_compute_get_payslip_mail")
    is_last_month = fields.Boolean("Last Month", compute="_compute_get_last_month")
    dec_basic_salary = fields.Float(
        string="Basic Salary 13",
        compute="_compute_get_dec_basic",
    )
    dec_hra = fields.Float(
        string="Basic Salary 13",
        compute="_compute_get_dec_basic",
    )
    food_allowance = fields.Float(compute="_compute_day_allowance", store=True)
    transport_allowance = fields.Float(compute="_compute_day_allowance", store=True)

    @api.depends("state")
    def _compute_day_allowance(self):
        for slip in self:
            entitle_employee_rec = self.env["entitle.employee.days"].search(
                [
                    ("start_date", ">=", slip.date_from),
                    ("end_date", "<=", slip.date_to),
                    ("state", "=", "confirmed"),
                ]
            )
            employee_data_ids_rec = entitle_employee_rec.employee_data_ids.filtered(
                lambda r: r.employee_name == slip.employee_id.name
            )
            if employee_data_ids_rec and slip.contract_id:
                slip.food_allowance = (
                    employee_data_ids_rec.entitle_days * slip.contract_id.food_allowance
                )
                slip.transport_allowance = slip.contract_id.transport_allowance
            else:
                slip.food_allowance = 0
                slip.transport_allowance = 0

    def seniority_of_month(self):
        end_date = datetime.now()
        start_date = self.contract_id.date_start
        num_months = (end_date.year - start_date.year) * 12 + (
            end_date.month - start_date.month
        )
        return num_months

    @api.depends("employee_id", "date_to", "contract_id")
    def _compute_last_year_total_salary(self):
        for slip in self:
            total = 0
            if slip.contract_id:
                contract = slip.contract_id

                contract_date_start_object = datetime.strptime(
                    str(contract.date_start), "%Y-%m-%d"
                )
                slip_date_to_object = datetime.strptime(str(slip.date_to), "%Y-%m-%d")
                if slip_date_to_object.year - contract_date_start_object.year >= 3:
                    if slip.employee_id:
                        date_to = datetime.strptime(str(slip.date_to), "%Y-%m-%d")
                        first_day = (date_to - relativedelta(months=12)).replace(day=1)
                        last_day = first_day + relativedelta(day=1, months=+12, days=-1)
                        slip_ids = self.env["hr.payslip"].search(
                            [
                                ("date_to", ">=", first_day),
                                ("date_to", "<=", last_day),
                                ("state", "=", "done"),
                            ]
                        )
                        for slips in slip_ids:
                            total += sum(
                                [
                                    line.total
                                    for line in slips.line_ids
                                    if line.code == "GROSS"
                                ]
                            )
                    slip.last_year_total_salary = total

    @api.depends("date_to")
    def _compute_is_january(self):
        for slip in self:
            slip.is_january = fields.Date.from_string(slip.date_to).month == 1

    def _compute_get_work_percentage(self):
        for slip in self:
            perc = 1
            if slip.contract_id:
                contract = slip.contract_id
                contract_date_start_object = datetime.strptime(
                    str(contract.date_start), "%Y-%m-%d"
                )
                slip_date_to_object = datetime.strptime(str(slip.date_to), "%Y-%m-%d")
                if (
                    contract_date_start_object.month == slip_date_to_object.month
                    and contract_date_start_object.year == slip_date_to_object.year
                ):
                    slip_date_from_object = datetime.strptime(
                        str(slip.date_from), "%Y-%m-%d"
                    )
                    slip_delta = slip_date_to_object - slip_date_from_object
                    slip_days = slip_delta.days + 1
                    contract_delta = slip_date_to_object - contract_date_start_object
                    contract_days = contract_delta.days + 1
                    if slip_days > 0:
                        perc = contract_days / slip_days
            slip.work_perc = perc

    # Form view - Send by email button logic
    def send_by_email(self):
        for i in self:
            if self.filtered(lambda x: x.state not in ("done")):
                raise UserError(_("Draft payslips can not be sent to employees"))
            payslip_mail = (
                self.env["ir.config_parameter"].sudo().get_param("send_payslip_mail")
            )
            if not payslip_mail:
                raise UserError(
                    _("Please check the configuration to send the payslip by mail")
                )
            template = self.env.ref("xe_kenya_hr_payroll.email_template_hr_payslip")
            email_to = i.employee_id.work_email
            email_from = self.env.user.email
            email_values = {"email_to": email_to, "email_from": email_from}
            mail_send = template.send_mail(
                i.id, email_values=email_values, force_send=True
            )
            return True

    def server_action_payslip_done(self):
        for record in self.filtered(lambda x: x.state == "draft"):
            record.with_context(payslip_generate_pdf=True).action_payslip_done()

    # List view - Send by email logic
    def send_by_email_action(self):
        if self.filtered(lambda x: x.state not in ("done")):
            raise UserError(_("Draft payslips can not be sent to employees"))
        payslip_mail = (
            self.env["ir.config_parameter"].sudo().get_param("send_payslip_mail")
        )
        if not payslip_mail:
            raise UserError(
                _("Please check the configuration to send the payslip by mail")
            )
        payslip_rec = (
            self.env["hr.payslip"]
            .sudo()
            .search(
                [
                    ("id", "in", self.env.context.get("active_ids")),
                    ("state", "=", "done"),
                ]
            )
        )
        for i in payslip_rec:
            template = self.env.ref("xe_kenya_hr_payroll.email_template_hr_payslip")
            email_to = i.employee_id.work_email
            email_from = self.env.user.email
            email_values = {"email_to": email_to, "email_from": email_from}
            mail_send = template.send_mail(
                i.id, email_values=email_values, force_send=True
            )

    def _convert_to_local_timezone(self, time):
        """
        Converts time as per local timezone.
        """
        if time:
            timezone = pytz.timezone("Asia/Kolkata")
            utc_in_time = pytz.utc.localize(
                datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
            )
            local_time = utc_in_time.astimezone(timezone)
            return local_time

    def float_time_convert(self, float_val):
        hours = math.floor(abs(float_val))
        mins = abs(float_val) - hours
        mins = round(mins * 60)
        if mins >= 60.0:
            hours = hours + 1
            mins = 0.0
        float_time = "%02d:%02d" % (hours, mins)
        return float_time

    def get_all_attendances(self):
        return self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee_id.id)], order="check_in asc"
        )

    def adjust_long_term_amount(self, long_term_amount):
        payslip_obj = self
        payslip_line = self.env["hr.payslip.line"]
        net_salary_rule_id = (
            self.env["hr.salary.rule"].search([("code", "=", "NET")]).id
        )
        net_line = payslip_line.search(
            [
                ("slip_id", "=", payslip_obj.id),
                ("salary_rule_id", "=", net_salary_rule_id),
            ]
        )
        net_amount = net_line.amount + long_term_amount
        net_line.write({"amount": net_amount})

    def calculate_longtermadvance(self):
        payslip_obj = self
        payslip_line = self.env["hr.payslip.line"]
        employee_id = payslip_obj.employee_id and payslip_obj.employee_id.id
        date_from = payslip_obj.date_from
        date_to = payslip_obj.date_to
        advance_lines = self.env["hr.long.term.advance.line"].search(
            [
                ("employee_id", "=", employee_id),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("payslip_id", "=", False),
            ]
        )

        long_term_amount_tot = 0
        for line in advance_lines:
            if line.mode == "add":
                salary_rule_id = self.env.ref(
                    "xe_kenya_hr_payroll.hr_rule_longtermadvance"
                ).id
            else:
                salary_rule_id = self.env.ref(
                    "xe_kenya_hr_payroll.hr_rule_longtermadvance_ded"
                ).id
                long_term_amount_tot = long_term_amount_tot + line.amount
            salary_rule_obj = self.env["hr.salary.rule"].browse(salary_rule_id)

            payslip_line.create(
                {
                    "name": salary_rule_obj.name,
                    "code": salary_rule_obj.code,
                    "category_id": salary_rule_obj.category_id
                    and salary_rule_obj.category_id.id,
                    "contract_id": self.contract_id.id,
                    "slip_id": self.id,
                    "quantity": 1,
                    "sequence": salary_rule_obj.sequence,
                    "salary_rule_id": salary_rule_id,
                    "amount": line.amount,
                    "long_term_advance_subline_id": line.id,
                }
            )
        long_term_amount_tot = -1 * long_term_amount_tot
        return long_term_amount_tot

    def compute_sheet2(self):
        for payslip in self:
            payslip.line_ids.unlink()
            long_term_amount = payslip.calculate_longtermadvance()

            payslip_lines_zero_value = self.env["hr.payslip.line"].search(
                [("slip_id", "=", payslip.id), ("total", "=", 0)]
            )

            if payslip_lines_zero_value:
                payslip_lines_zero_value.unlink()
            generic_struct_id = self.env.ref("xe_kenya_hr_payroll.structure_002").id
            if (
                payslip.employee_id.emp_type == "international"
                and generic_struct_id == payslip.struct_id.id
            ):
                payslip_lines_paye = self.env["hr.payslip.line"].search(
                    [("slip_id", "=", payslip.id), ("code", "=", "PAYE")]
                )
                if payslip_lines_paye:
                    payslip_lines_paye.unlink()
            # payslip_lines_hra and amount_total not define
            # payslip_lines_hra.write({"amount": amount_total})
            payslip.adjust_long_term_amount(long_term_amount)
        return True

    # Get Food allowance and transport allowance value
    def _get_payslip_lines1(self):
        self.ensure_one()

        localdict = self.env.context.get("force_payslip_localdict", None)
        if localdict is None:
            localdict = self._get_localdict()

        rules_dict = localdict["rules"].dict
        result_rules_dict = localdict["result_rules"].dict

        blacklisted_rule_ids = self.env.context.get(
            "prevent_payslip_computation_line_ids", []
        )

        result = {}
        for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
            if rule.id in blacklisted_rule_ids:
                continue
            localdict.update({"result": None, "result_qty": 1.0, "result_rate": 100})
            if rule._satisfy_condition(localdict):
                amount, qty, rate = rule._compute_rule(localdict)
                # check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                # set/overwrite the amount computed for this rule in the localdict
                tot_rule = amount * qty * rate / 100.0
                localdict[rule.code] = tot_rule
                result_rules_dict[rule.code] = {
                    "total": tot_rule,
                    "amount": amount,
                    "quantity": qty,
                }
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = rule.category_id._sum_salary_rule_category(
                    localdict, tot_rule - previous_amount
                )
                # Retrieve the line name in the employee's lang
                employee_lang = self.employee_id.sudo().lang
                if rule.code in [
                    "BASIC",
                    "GROSS",
                    "NET",
                ]:  # Generated by default_get (no xmlid)
                    if rule.code == "BASIC":
                        rule_name = _("Basic Salary")
                    elif rule.code == "GROSS":
                        rule_name = _("Gross")
                    elif rule.code == "NET":
                        rule_name = _("Net Salary")
                else:
                    rule_name = rule.with_context(lang=employee_lang).name

                result[rule.code] = {
                    "sequence": rule.sequence,
                    "code": rule.code,
                    "name": rule_name,
                    "note": rule.note,
                    "salary_rule_id": rule.id,
                    "contract_id": localdict["contract"].id,
                    "employee_id": localdict["employee"].id,
                    "amount": amount,
                    "quantity": qty,
                    "rate": rate,
                    "slip_id": self.id,
                }
        return result.values()


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    date_created = fields.Date(compute="_compute_today_date", store=True)
    long_term_advance_subline_id = fields.Many2one(
        "hr.long.term.advance.line", "Long Term Subline"
    )

    def _compute_today_date(self):
        return datetime.now()
