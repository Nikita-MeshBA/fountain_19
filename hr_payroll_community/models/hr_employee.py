# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    """Inherit hr_employee for getting Payslip Counts"""
    _inherit = 'hr.employee'
    _description = 'Employee'

    slip_ids = fields.One2many('hr.payslip',
                               'employee_id', string='Payslips',
                               readonly=True,
                               help="Choose Payslip for Employee")
    payslip_count = fields.Integer(compute='_compute_payslip_count',
                                   string='Payslip Count',
                                   help="Set Payslip Count")

    def _compute_payslip_count(self):
        """Function for count Payslips"""
        payslip_data = self.env['hr.payslip'].sudo()._read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'], ['__count'])
        result = {employee.id: count for employee, count in payslip_data}
        for employee in self:
            employee.payslip_count = result.get(employee.id, 0)
