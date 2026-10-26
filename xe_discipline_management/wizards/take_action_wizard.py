# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TakeAction(models.TransientModel):
    _name = "xe.take.action"
    _description = "Take Action Based on Misbehaviour"

    is_fine = fields.Boolean("Fine")
    fine_amount = fields.Integer()
    is_suspend = fields.Boolean("Suspend")
    suspend_from_date = fields.Date()
    suspend_to_date = fields.Date()
    remarks = fields.Text()
    discipline_id = fields.Many2one("xe.discipline.records", string="Discipline Record")

    @api.constrains("suspend_from_date", "suspend_to_date")
    def check_dates(self):
        if self.is_suspend:
            for record in self:
                if (
                    record.suspend_from_date
                    and record.suspend_to_date
                    and record.suspend_from_date > record.suspend_to_date
                ):
                    raise ValidationError(_("To Date cannot be set before From Date."))

    def take_action(self):
        discipline = self.env["xe.discipline.records"].browse(
            [self.env.context.get("active_id", False)]
        )
        if self.is_fine and not self.is_suspend:
            self.get_fine_data(discipline)
        elif self.is_suspend and not self.is_fine:
            self.get_suspend_data(discipline)
        elif self.is_suspend and self.is_fine:
            self.get_fine_data(discipline)
            self.get_suspend_data(discipline)
        else:
            discipline.state = "done"
        return True

    def get_suspend_data(self, discipline):
        suspend = self.env["xe.suspended.students"].create(
            {
                "student_id": discipline.student_id.id,
                "date_from": self.suspend_from_date,
                "date_to": self.suspend_to_date,
                "misbehave_categ_id": discipline.misbehave_categ_id.id,
                "discipline_id": discipline.id,
            }
        )
        template = self.env.ref(
            "xe_discipline_management.email_suspension_from_school_template", False
        )
        template.send_mail(suspend.id, force_send=True)
        discipline.state = "suspended"

    def get_fine_data(self, discipline):
        account = self.env["account.account"]
        invoice_line_account = account.search(
            [("account_type", "=", "expense")], limit=1
        ).id
        product = self.env.ref("xe_discipline_management.misbehave_fine_product")
        invoice_line_vals = {
            "product_id": product.id,
            "name": product.name,
            "quantity": 1.0,
            "price_unit": self.fine_amount,
            "discount": 0.0,
            "account_id": invoice_line_account,
        }
        invoice_line_ids = [(0, 0, invoice_line_vals)]
        self.env["account.move"].create(
            {
                "partner_id": discipline.student_id.partner_id.id,
                "move_type": "out_invoice",
                "invoice_date": fields.date.today(),
                "invoice_line_ids": invoice_line_ids,
            }
        )
        discipline.state = "done"
