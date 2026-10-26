# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import api, fields, models


class GeneralSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attendance_type = fields.Selection(
        [
            ("daily_1", "Daily One-time"),
            ("daily_2", "Morning and Afternoon"),
            ("subject_wise", "Subject-wise"),
        ],
        "Type of Attendance",
        default="daily_1",
    )
    sunday_bool = fields.Boolean()
    monday_bool = fields.Boolean()
    tuesday_bool = fields.Boolean()
    wednesday_bool = fields.Boolean()
    thursday_bool = fields.Boolean()
    friday_bool = fields.Boolean()
    saturday_bool = fields.Boolean()

    @api.model
    def get_values(self):
        res = super(GeneralSettings, self).get_values()
        get_param = self.env["ir.config_parameter"].sudo().get_param

        res.update(
            attendance_type=get_param("xe_attendance_management.attendance_type")
        )
        res.update(sunday_bool=get_param("xe_attendance_management.sunday_bool"))
        res.update(monday_bool=get_param("xe_attendance_management.monday_bool"))
        res.update(tuesday_bool=get_param("xe_attendance_management.tuesday_bool"))
        res.update(wednesday_bool=get_param("xe_attendance_management.wednesday_bool"))
        res.update(thursday_bool=get_param("xe_attendance_management.thursday_bool"))
        res.update(friday_bool=get_param("xe_attendance_management.friday_bool"))
        res.update(saturday_bool=get_param("xe_attendance_management.saturday_bool"))
        return res

    def set_values(self):
        super(GeneralSettings, self).set_values()
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("xe_attendance_management.attendance_type", self.attendance_type)
        set_param("xe_attendance_management.sunday_bool", self.sunday_bool)
        set_param("xe_attendance_management.monday_bool", self.monday_bool)
        set_param("xe_attendance_management.tuesday_bool", self.tuesday_bool)
        set_param("xe_attendance_management.wednesday_bool", self.wednesday_bool)
        set_param("xe_attendance_management.thursday_bool", self.thursday_bool)
        set_param("xe_attendance_management.friday_bool", self.friday_bool)
        set_param("xe_attendance_management.saturday_bool", self.saturday_bool)
