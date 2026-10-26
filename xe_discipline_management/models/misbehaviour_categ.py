# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MisbehaviourCategory(models.Model):
    _name = "xe.misbehave.category"
    _description = "Misbehaviour Category"

    name = fields.Char()
    category_type = fields.Selection([("minor", "Minor"), ("major", "Major")])
    email_tmpl_id = fields.Many2one("mail.template", "Template")
    sub_category_ids = fields.One2many(
        "xe.misbehave.sub.category", "category_id", string="Sub Categories"
    )


class MisbehaviourSubCategory(models.Model):
    _name = "xe.misbehave.sub.category"
    _description = "Misbehaviour Sub Category"

    name = fields.Char()
    category_id = fields.Many2one("xe.misbehave.category", "Misbehave Categories")
