# -*- coding: utf-8 -*-
###############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import fields, models, api


class HRHELB(models.Model):
    _name = "hr.helb"
    _description = "Higher Education Loan Board"

    @api.depends("amount", "duration")
    def _compute_deduction(self):
        for helb in self.filtered(lambda rec: not rec.duration):
            helb.amount_deduct = helb.amount / float(helb.duration) or 0.0

    employee_id = fields.Many2one("hr.employee", string="Employee")
    name = fields.Char(required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    amount = fields.Monetary(string="Loan Amount")
    amount_deduct = fields.Monetary(
        string="Amount to Deduct (/Month)", compute="_compute_deduction", store=True
    )
    duration = fields.Integer(default=1)
    deduction_applied = fields.Integer()
