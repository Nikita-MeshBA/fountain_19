# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class LibraryCardType(models.Model):
    _name = "xe.library.card.type"
    _description = "Library Card Type"

    name = fields.Char()
    allow_media = fields.Integer("Allowed Media")

    type = fields.Selection(
        [("student", "Student"), ("others", "Others")], default="student"
    )
    duration = fields.Integer(
        help="Duration in terms of Number of Lead Days",
    )
    is_penalty = fields.Boolean("Generate Penalty")
    penalty_amt_per_day = fields.Float("Penalty Amount / Day")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    product_id = fields.Many2one("product.product")

    @api.constrains("allow_media", "duration", "penalty_amt_per_day")
    def check_details(self):
        if (
            self.allow_media < 0
            or self.duration < 0.0
            or self.penalty_amt_per_day < 0.0
        ):
            raise ValidationError(_("Enter proper value"))


class LibraryCard(models.Model):
    _name = "xe.library.card"
    _rec_name = "number"
    _description = "Library Card"

    partner_id = fields.Many2one("res.partner", "Student/Faculty")
    number = fields.Char(readonly=True)
    library_card_type_id = fields.Many2one("xe.library.card.type", "Card Type")
    issue_date = fields.Date(default=fields.Date.today())
    student_id = fields.Many2one("xe.student", domain=[("library_card_id", "=", False)])
    faculty_id = fields.Many2one(
        "hr.employee", domain=[("library_card_id", "=", False)]
    )
    course_id = fields.Many2one("xe.course", "Class")
    batch_id = fields.Many2one("xe.term", "Term")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    type = fields.Selection(related="library_card_type_id.type")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("student_id"):
                student = self.env["xe.student"].browse(vals.get("student_id"))
                vals["partner_id"] = student.partner_id.id
            if vals.get("faculty_id"):
                teacher = self.env["hr.employee"].browse(vals.get("faculty_id"))
                vals["partner_id"] = teacher.user_partner_id.id

            if vals.get("number") and self.search([("number", "=", vals.get("number")), ("company_id", "=", self.env.company.id)]):
                raise ValidationError(
                    _("Library card number %s already exists. Number should be unique per card!" % (vals.get("number")))
                )

        records = super(LibraryCard, self).create(vals_list)
        for res in records:
            if res.library_card_type_id.type == "student":
                res.student_id.library_card_id = res
            else:
                res.faculty_id.library_card_id = res
        return records

    @api.onchange("type")
    def onchange_type(self):
        if self.type == "student":
            self.faculty_id = False
        else:
            self.student_id = False

    @api.onchange("course_id")
    def _onchange_course_batch(self):
        student_course = self.env["xe.student"].search(
            [
                ("course_id", "=", self.course_id.id),
            ]
        )
        student_ids = student_course.ids
        return {"domain": {"student_id": [("id", "in", student_ids)]}}
