# -*- coding: utf-8 -*-
##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
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
##############################################################################

from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _


class HrContract(models.Model):
    # _inherit = "hr.contract"
    _inherit = "hr.version"
    @api.depends("employee_id.birthday")
    def _compute_age(self):
        for rec in self:
            if rec.employee_id.birthday:
                birthday_str = rec.employee_id.birthday.strftime("%Y-%m-%d")
                birthday = datetime.strptime(birthday_str, "%Y-%m-%d")
                current_date = datetime.now()
                days = (current_date - birthday).days
                age = int(round(float(days / 365)))
                rec.age = age
            else:
                rec.age = 0

    def age_compute(self):
        if self.employee_id.birthday:
            birthday_str = self.employee_id.birthday.strftime("%Y-%m-%d")
            birthday = datetime.strptime(birthday_str, "%Y-%m-%d")
            current_date = datetime.now()
            days = (current_date - birthday).days
            age = int(round(float(days / 365)))
            self.age = age
        else:
            self.age = 0

    communication = fields.Monetary(digits=(16, 2), help="Communication")
    loan_benefit = fields.Monetary(digits=(16, 2))
    tax_credit = fields.Monetary(digits=(16, 2))
    wcif = fields.Monetary(string="W.C.I.F", digits=(16, 2), help="W.C.I.F")
    medical_aid = fields.Monetary(digits=(16, 2))
    nsa = fields.Monetary(string="NSSA", digits=(16, 2), default=11.41)
    aids_levy = fields.Monetary(digits=(16, 2), help="Aids Levy")
    pension_old_mutual = fields.Monetary(digits=(16, 2))
    loan = fields.Monetary(digits=(16, 2))
    house_allowance = fields.Monetary(digits=(16, 2))
    bonus = fields.Monetary(digits=(16, 2))
    age = fields.Integer(compute="_compute_age", store=True)
    transport_allowance = fields.Monetary(digits=(16, 2))
    schoolfees_deduction = fields.Monetary(string="School Fees", digits=(16, 2))
