# -*- coding: utf-8 -*-

# pylint: disable=E0401

from datetime import datetime

from odoo import api, fields, models


class MSReportWizard(models.TransientModel):
    _name = "ms.report.wizard"
    _description = "ms.report.wizard"

    def get_years():
        year_list = []
        for i in range(2016, 2036):
            year_list.append((str(i), str(i)))
        return year_list

    month = fields.Selection(
        [
            ("January", "January"),
            ("February", "February"),
            ("March", "March"),
            ("April", "April"),
            ("May", "May"),
            ("June", "June"),
            ("July", "July"),
            ("August", "August"),
            ("September", "September"),
            ("October", "October"),
            ("November", "November"),
            ("December", "December"),
        ]
    )
    year = fields.Selection(get_years())
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
            ("verify", "Waiting"),
            ("all", "All"),
        ],
        default="all",
        required=True,
    )
    salary_structure_id = fields.Many2one("hr.payroll.structure")

    def get_xlsx_report(self):
        payslip_month = str(self.month) + "-" + str(self.year)
        report_name = "Monthly Salary Report-" + payslip_month + ".xlsx"
        data = {
            "salary_structure_id": self.salary_structure_id.id,
            "ids": self.ids,
            "model": self._name,
            "payslip_month": payslip_month,
            "state": self.state,
            "form": {
                "date_start": self.month,
                "date_end": self.year,
            },
        }
        report_id = self.env.ref("xe_kenya_hr_payroll.ms_xlsx_report").id
        report = self.env["ir.actions.report"].search([("id", "=", report_id)])
        report.report_file = report_name
        return self.env.ref("xe_kenya_hr_payroll.ms_xlsx_report").report_action(
            self, data=data
        )


class ReportMS(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = "report.xe_kenya_hr_payroll.ms_report_view"
    _description = "MS Report View"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data["form"]["date_start"]
        date_end = data["form"]["date_end"]

        docs = []
        employees = self.env["hr.employee"].search([], order="name asc")
        for employee in employees:
            nssf_amount = self.env["hr.payslip.line"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("code", "=", "NSSF"),
                ]
            )
            vol_amount = self.env["hr.payslip.line"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("code", "=", "PENS"),
                ]
            )
            date = self.env["hr.payslip"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("state", "=", "done"),
                ]
            )

            for nssf_date in date:
                create_date_datetime_object = datetime.strptime(
                    nssf_date.date_from, "%Y-%m-%d"
                )
                if (
                    create_date_datetime_object.month == date_start
                    and create_date_datetime_object.year == date_end
                ):
                    for nssf_total in nssf_amount:
                        nssf_sum = nssf_total.total
                    for vol_total in vol_amount:
                        vol_sum = vol_total.total

                    total = nssf_sum + vol_sum
                    docs.append(
                        {
                            "payroll_no": employee.employee_no,
                            "employee": employee.name,
                            "id_no": employee.identification_id,
                            "pin_no": employee.pin_no,
                            "nssf_no": employee.nssf_no,
                            "amount": nssf_sum,
                            "vol_sum": vol_sum,
                            "total": total,
                        }
                    )

        return {
            "doc_ids": data["ids"],
            "doc_model": data["model"],
            "docs": docs,
        }
