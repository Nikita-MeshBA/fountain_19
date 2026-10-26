# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    def _compute_payslip_count(self):
        for employee in self:
            payslip_ids = self.env["hr.payslip"].search(
                [("employee_id", "=", employee.id), ("state", "=", "done")]
            )
            employee.payslip_count = len(payslip_ids)

    def _compute_contracts_count(self):
        contract_data = (
            self.env["hr.version"]
            .sudo()
            ._read_group(
                [("employee_id", "in", self.ids)], ["employee_id"], ["__count"]
            )
        )
        result = {employee.id: count for employee, count in contract_data}
        for employee in self:
            employee.contracts_count = result.get(employee.id, 0)

    contracts_count = fields.Integer(
        compute="_compute_contracts_count", string="Contract Count"
    )
    payslip_count = fields.Integer(compute="_compute_payslip_count")
