# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class XeProgressBook(models.Model):
    _name = "xe.progress.book"
    _description = "Progress Book"

    name = fields.Char(
        default=lambda self: _("New"),
        copy=False,
        readonly=True,
        required=True,
        index=True,
    )
    student_id = fields.Many2one("xe.student")
    roll_number = fields.Char("Admission Number", related="student_id.roll_number")
    course_id = fields.Many2one("xe.course")
    classroom_id = fields.Many2one("xe.classroom")
    image_1920 = fields.Image("Image", related="student_id.image_1920")
    academic_year_id = fields.Many2one(
        "xe.academic.year", related="student_id.current_academic_year_id"
    )
    state = fields.Selection(
        [("draft", "Draft"), ("in_process", "In Process"), ("validate", "Validate")],
        default="draft",
    )
    progress_book_line_ids = fields.One2many(
        "xe.progress.book.line", "progress_book_id"
    )

    @api.model
    def create(self, vals):
        """Create new Sequence"""
        if vals.get("name", "New") == "New":
            student_id = self.env["xe.student"].search(
                [("id", "=", vals.get("student_id"))]
            )
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("xe.progress.book")
                + "/"
                + student_id.name
            )
        res = super(XeProgressBook, self).create(vals)
        return res

    @api.onchange("course_id")
    def _onchange_course_id(self):
        if self.course_id:
            self.classroom_id = False
            self.student_id = False
            classroom_ids = self.env["xe.classroom"].search(
                [("course_id", "=", self.course_id.id)]
            )
            return {"domain": {"classroom_id": [("id", "in", classroom_ids.ids)]}}

    @api.onchange("classroom_id")
    def _onchange_classroom_id(self):
        if self.classroom_id:
            self.student_id = False
            student_ids = self.env["xe.student"].search(
                [("classroom_id", "=", self.classroom_id.id)]
            )
            return {"domain": {"student_id": [("id", "in", student_ids.ids)]}}


class XeProgressBookLine(models.Model):
    _name = "xe.progress.book.line"
    _description = "Progress Book Line"

    name = fields.Text()
    progress_book_id = fields.Many2one("xe.progress.book")
    types = fields.Selection([("ee", "EE"), ("me", "ME"), ("ae", "AE"), ("be", "BE")])
    comments = fields.Text()
    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
