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


from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class ZimbabweLongTermAdvance(models.Model):
    _name = "zimbabwe.hr.long.term.advance"
    _description = "Long Term Advance"

    @api.constrains("date", "duration", "amount", "amount_deduct")
    def _check_end_date(self):
        for record in self:
            if record.duration <= 0:
                raise ValidationError(_("Duration must be greater than 0!"))
            payslip_check = self.env["hr.payslip"].search(
                [
                    ("date_from", ">=", record.date),
                    ("date_to", "<=", record.date),
                    ("employee_id", "=", record.employee_id and record.employee_id.id),
                ]
            )
            if payslip_check:
                raise ValidationError(
                    _("Payslip already generated for the Date selected!")
                )

    @api.depends("amount", "duration")
    def _compute_deduction(self):
        for advance in self.filtered(lambda rec: not rec.duration):
            advance.amount_deduct = advance.amount / float(advance.duration) or 0.0

    @api.depends("advance_sub_line_ids", "advance_sub_line_ids.payslip_id")
    def _compute_payslip(self):
        for line in self.advance_sub_line_ids:
            if line.payslip_id and line.payslip_id.id:
                self.considered_in_payslip = True

    considered_in_payslip = fields.Boolean(
        string="Processed", compute="_compute_payslip", store=True
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")
    name = fields.Char(required=True)
    date = fields.Date(required=True, default=fields.Datetime.now)
    amount = fields.Float()
    duration = fields.Integer(default=1)
    amount_deduct = fields.Float(
        string="Monthly Amount to Deduct", compute="_compute_deduction", store=True
    )
    advance_sub_line_ids = fields.One2many(
        "zimbabwe.hr.long.term.advance.line",
        "advance_id",
        string="Advance Subline",
        copy=False,
    )

    def unlink(self):
        subline = self.advance_sub_line_ids
        for line in subline:
            if line.payslip_id and line.payslip_id.id:
                raise UserError(
                    _("You cannot delete this,it is already included in Payslip")
                )
        return super(ZimbabweLongTermAdvance, self).unlink()

    def create_sub_lines(self):
        for record in self:
            sublines = record.advance_sub_line_ids
            if sublines:
                sublines.unlink()
            for i in range(0, record.duration):
                date = str(record.date + relativedelta(months=i))[:10]
                sub_line_vals = {
                    "employee_id": record.employee_id and record.employee_id.id,
                    "advance_id": record.id,
                    "date": date,
                    "amount": record.amount_deduct,
                    "mode": "deduct",
                }
                self.env["zimbabwe.hr.long.term.advance.line"].create(sub_line_vals)

    @api.model_create_multi
    def create(self, values):
        record = super(ZimbabweLongTermAdvance, self).create(values)
        record.create_sub_lines()
        return record

    def write(self, values):
        result = super(ZimbabweLongTermAdvance, self).write(values)
        self.create_sub_lines()
        return result


class ZimbabweLongTermAdvanceSubLine(models.Model):
    _name = "zimbabwe.hr.long.term.advance.line"
    _description = "Long Term Advance SubLine"

    employee_id = fields.Many2one("hr.employee", string="Employee", readonly=True)
    advance_id = fields.Many2one(
        "zimbabwe.hr.long.term.advance", string="Advance Line ID", ondelete="cascade"
    )
    date = fields.Date(
        readonly=True,
    )
    amount = fields.Float(readonly=True)
    mode = fields.Selection(
        [("add", "Add"), ("deduct", "Deduct")], string="Add/Deduction"
    )
    payslip_id = fields.Many2one("hr.payslip", string="Payslip")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("verify", "Waiting"),
            ("done", "Done"),
            ("cancel", "Rejected"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        default="draft",
        related="payslip_id.state",
    )
