from odoo import models, fields


class XeMarking(models.Model):
    _name = "xe.marking"
    _description = "Student Marking"
    _rec_name = "marking_id"

    marking_id = fields.Char(
        string="Marking ID",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("xe.marking"),
    )
    student_id = fields.Many2one("xe.student", required=True)
    course_id = fields.Many2one(
        "xe.course", related="student_id.course_id", required=True
    )
    classroom_id = fields.Many2one(
        "xe.classroom", related="student_id.classroom_id", required=True
    )
    academic_term_id = fields.Many2one(
        "xe.academic.terms", related="rubric_id.term_id", string="Term", store=True
    )
    strand_id = fields.Many2one(
        "xe.strand", related="rubric_id.strand_id", string="Strand", store=True
    )
    theme_id = fields.Many2one(
        "xe.theme", related="rubric_id.theme_id", string="Theme", store=True
    )
    subject_id = fields.Many2one(
        "xe.subject", related="rubric_id.subject_id", string="Subject", store=True
    )
    rubric_id = fields.Many2one("xe.rubric", string="Rubric", required=True)
    substrand_id = fields.Many2one("xe.substrand", related="rubric_id.substrand_id")
    rubric_activity = fields.Text(string="Activity")
    grade = fields.Selection(
        [("EE", "EE"), ("AE", "AE"), ("ME", "ME"), ("BE", "BE")],
    )
    comment = fields.Text()

    _sql_constraints = [
        ("marking_id_uniq", "unique (marking_id)", "Marking ID must be unique!")
    ]
