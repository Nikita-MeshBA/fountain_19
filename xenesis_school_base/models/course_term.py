from odoo.exceptions import ValidationError

from odoo import api, fields, models, _


class CourseDetails(models.Model):
    _name = "xe.course"
    _inherit = ["mail.thread"]
    _description = "Course Details"

    def _get_sequence(self):
        is_sequence = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xenesis_school_base.class_admission_no_automatic")
            or False
        )
        return is_sequence

    def _sequence_Admission(self):
        admission_seq = (
            self.env["ir.sequence"]
            .sudo()
            .search([("code", "=", "xe.admission.enquiry")], limit=1)
        )
        return admission_seq.id

    name = fields.Char()
    code = fields.Char()
    section = fields.Char()
    attendance = fields.Float(string="Minimum Attendance(%)")
    description = fields.Text()
    course_subject_line_ids = fields.Many2many("xe.subject", string="Class Subject Details")
    is_sequence = fields.Boolean(default=_get_sequence)
    classroom_seq_id = fields.Many2one(
        "ir.sequence", string="Sequence", default=_sequence_Admission
    )
    company_id = fields.Many2one(
        "res.company",
        index=True,
        default=lambda self: self.env.company,
    )

    def action_view_terms(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "xenesis_school_base.act_term1"
        )
        action["domain"] = [
            ("course_id", "=", self.id),
        ]
        action["context"] = {"default_course_id": self.id}
        return action


class TermDetails(models.Model):
    _name = "xe.term"
    _inherit = ["mail.thread"]
    _description = "Term Details"

    course_id = fields.Many2one("xe.course", string="Class")
    name = fields.Char()
    code = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    max_student = fields.Float(string="Maximum Number of Student")
    term_subject_line_ids = fields.One2many("xe.tsd", "term_id", "Term Subject Details")
    company_id = fields.Many2one(
        "res.company",
        index=True,
        default=lambda self: self.env.company,
    )


class ClassTeacherAllocation(models.Model):
    _name = "xe.cta"
    _inherit = ["mail.thread"]
    _description = "Class Teacher Allocation"
    _rec_name = "course_id"

    course_id = fields.Many2one("xe.course", string="Class")
    term_id = fields.Many2one("xe.term")
    teacher_id = fields.Many2one("hr.employee")

    @api.model
    def create(self, vals):
        teacher = self.env["hr.employee"].browse(vals.get("teacher_id"))
        course_id = teacher.assigned_course_id and teacher.assigned_course_id.id
        term_id = teacher.assigned_term_id and teacher.assigned_term_id.id
        if term_id or course_id:
            raise ValidationError(
                _("Already assigned Class and term for teacher: %s.", teacher.name)
            )
        teacher.assigned_course_id = vals.get("course_id")
        teacher.assigned_term_id = vals.get("term_id")
        result = super(ClassTeacherAllocation, self).create(vals)
        return result


class ClassSubjectDetails(models.Model):
    _name = "xe.csd"
    _description = "Class Subject Details"

    course_id = fields.Many2one("xe.course", string="Class", ondelete="cascade")
    name = fields.Char()
    code = fields.Char()
    term_id = fields.Many2one("xe.term")
    subject_type = fields.Selection(
        [
            ("theory", "Theory"),
            ("practical", "Practical"),
            ("both", "Both"),
            ("other", "Other"),
        ],
        "Type",
        default="theory",
    )


class TermSubjectDetails(models.Model):
    _name = "xe.tsd"
    _description = "Term Subject Details"

    term_id = fields.Many2one("xe.term", ondelete="cascade")
    name = fields.Char()
    code = fields.Char()
    subject_type = fields.Selection(
        [
            ("theory", "Theory"),
            ("practical", "Practical"),
            ("both", "Both"),
            ("other", "Other"),
        ],
        "Type",
        default="theory",
    )
