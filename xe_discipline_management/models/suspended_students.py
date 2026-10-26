# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AchievementCategory(models.Model):
    _name = "xe.suspended.students"
    _inherit = ["mail.thread"]
    _description = "Suspended Students"
    _rec_name = "student_id"

    student_id = fields.Many2one("xe.student")
    date_from = fields.Date()
    date_to = fields.Date()
    misbehave_categ_id = fields.Many2one(
        "xe.misbehave.category", "Misbehaviour Category"
    )
    discipline_id = fields.Many2one("xe.discipline.records", "Discipline Record")
