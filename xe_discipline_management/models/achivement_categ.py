# -*- coding: utf-8 -*-

from odoo import models, fields


class AchievementCategory(models.Model):
    _name = "xe.achieve.category"
    _inherit = ["mail.thread"]
    _description = "Achievement Category"

    name = fields.Char()
