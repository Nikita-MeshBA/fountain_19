from odoo.exceptions import UserError

from odoo import api, fields, models, _


class SubjectDetails(models.Model):
    _name = "xe.subject"
    _description = "Subject Details"
    _inherit = ["mail.thread"]

    name = fields.Char()
    code = fields.Char()
    subject_mode = fields.Selection(
        [("yes", "Yes"), ("no", "No")], "Elective", default="no"
    )
    description = fields.Text()
    course_ids = fields.Many2many("xe.course", string="Class")
    company_id = fields.Many2one(
        "res.company",
        index=True,
        default=lambda self: self.env.company,
    )

    @api.constrains("code", "company_id")
    def _check_duplicates(self):
        for line in self:
            rec_count = self.search_count(
                [("company_id", "=", line.company_id.id), ("code", "=", line.code)]
            )
            if rec_count > 1:
                raise UserError(_("Code should be unique per subject!"))


class AssignSubject(models.Model):
    _name = "xe.assignsubject"
    _description = "Assign Subjects"
    _rec_name = "course_id"
    _inherit = ["mail.thread"]

    employee_id = fields.Many2one("hr.employee")
    course_id = fields.Many2one("xe.course", string="Class")
    classroom_ids = fields.Many2many("xe.classroom")
    term_id = fields.Many2one("xe.term")
    subject_ids = fields.Many2many("xe.subject", string="Subject(s)")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("assigned", "Assigned"),
        ],
        string="Status",
        default="draft",
    )

    def action_assign(self):
        subject_ids = self.subject_ids
        term_id = self.term_id and self.term_id.id or False
        course_id = self.course_id and self.course_id.id or False
        if not subject_ids:
            raise UserError(_("You didn't selected any subjects yet"))

        term_subject_array = []
        course_subject_array = []
        assigned_subjects = []
        for subject in subject_ids:
            term_vals = {}
            course_vals = {}
            name = subject.name
            code = subject.code
            subject_type = subject.subject_type
            term_vals = {
                "term_id": term_id,
                "name": name,
                "subject_type": subject_type,
                "code": code,
            }
            course_vals = {
                "term_id": term_id,
                "name": name,
                "subject_type": subject_type,
                "code": code,
                "course_id": course_id,
            }
            csd_obj = self.env["xe.csd"].search(
                [("code", "=", code), ("term_id", "=", term_id)]
            )
            tsd_obj = self.env["xe.csd"].search(
                [("code", "=", code), ("id", "=", term_id)]
            )
            if csd_obj:
                assigned_subjects.append(csd_obj.name)
            if tsd_obj:
                assigned_subjects.append(tsd_obj.name)
            term_subject_array.append(term_vals)
            course_subject_array.append(course_vals)
        if len(assigned_subjects) > 0:
            raise UserError(
                _("Following subject(s) :%s are already assigned to the course & term")
                % (list(set(assigned_subjects)))
            )
        self.env["xe.csd"].create(course_subject_array)
        self.env["xe.tsd"].create(term_subject_array)
        self.state = "assigned"
        return True


class ElectiveSubject(models.Model):
    _name = "xe.electivesubject"
    _description = "Elective Subjects"
    _rec_name = "course_id"
    _inherit = ["mail.thread"]

    course_id = fields.Many2one("xe.course", string="Class")
    term_id = fields.Many2one("xe.term")
    subject_id = fields.Many2one("xe.subject")
    student_ids = fields.Many2many("xe.student", string="Student Details")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("assigned", "Assigned"),
        ],
        string="Status",
        default="draft",
    )

    def action_assign(self):
        elective_subject_id = self.subject_id and self.subject_id.id or False
        student_ids = self.student_ids
        if not student_ids:
            raise UserError(_("You didn't selected any students yet"))

        for student in student_ids:
            if student.elective_subject_id and student.elective_subject_id.id:
                raise UserError(
                    _("Elective already selected for the student: %s") % student.name
                )
            student.elective_subject_id = elective_subject_id
        self.state = "assigned"
        return True
