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


class MisbehaviourType(models.TransientModel):
    _name = "misbehaviour.type"
    _description = "Misbehaviour Type"

    misbehaviour_type = fields.Selection(
        [("major", "Major"), ("minor", "Minor")], default="major", required=True
    )
    from_date = fields.Date(required=True, default=lambda self: fields.Date.today())
    to_date = fields.Date(required=True, default=lambda self: fields.Date.today())

    @api.constrains("from_date", "to_date")
    def check_dates(self):
        for record in self:
            from_date = fields.Date.from_string(record.from_date)
            to_date = fields.Date.from_string(record.to_date)
            if to_date < from_date:
                raise ValidationError(_("To Date cannot be set before From Date."))

    def print_report(self):
        data = self.read(["misbehaviour_type", "from_date", "to_date"])[0]
        return self.env.ref(
            "xe_discipline_management.action_report_misbehaviour_type"
        ).report_action(self, data=data)
