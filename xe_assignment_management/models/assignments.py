from lxml import etree
from datetime import datetime
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class Assignments(models.Model):
    _name = "xe.assignment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Assignments"

    @api.model
    def _get_teacher_id(self):
        for line in self:
            if line.create_teacher_id:
                teacher_id = (
                    self.env["hr.employee"]
                    .search([("user_id", "=", line.create_teacher_id.id)])
                    .id
                )
                if teacher_id:
                    return teacher_id

    name = fields.Char(tracking=True)
    course_id = fields.Many2one("xe.course", "Class", tracking=True)
    classroom_id = fields.Many2one("xe.classroom", string="Class Room", tracking=True)
    subject_id = fields.Many2one("xe.subject", tracking=True)
    assignment_type_id = fields.Many2one("xe.assignment.type")
    create_teacher_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user.id,
        string="Teacher",
        tracking=True,
    )
    teacher_id = fields.Many2one("hr.employee", default=_get_teacher_id)

    submit_date = fields.Datetime("Submission Date", tracking=True)
    total_marks = fields.Float(tracking=True)
    description = fields.Text(tracking=True)
    number = fields.Char(default="New")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("assigned", "Assigned"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    student_ids = fields.Many2many(
        "xe.student",
        "student_assignment_rel",
        "assignment_id",
        "student_id",
        string="Allocated Students",
    )
    domain_set_field = fields.Boolean(compute="_compute_domain_set_field")
    assignment_submissions_ids = fields.One2many(
        "xe.assignment.submission", "assignment_id", string="Submissions"
    )
    assigned_sub_ids = fields.Many2many(
        "xe.subject",
        "dummy_subj_rel",
        "assignment_id",
        "sub_id",
        string="Assigned Subjects",
        compute="_compute_subject_domain",
    )
    assigned_stud_ids = fields.Many2many(
        "xe.student",
        "student_dummy_rel",
        "assignment_id",
        "student_id",
        string="Assigned Students",
        compute="_compute_subject_domain",
        tracking=True,
    )
    student_user_ids = fields.Many2many(
        "res.users",
        "assign_stud_usr",
        "assgn_id",
        "user_id",
        compute="_compute_student_user",
        store=True,
    )

    issue_date = fields.Datetime(default=lambda self: fields.datetime.now())
    color = fields.Integer("Color Index")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    def unlink(self):
        for i in self:
            if i.state != "draft":
                raise UserError(
                    _("Record cannot be deleted, Assignmend state is " + i.state)
                )
        return super().unlink()

    @api.depends("student_ids")
    def _compute_student_user(self):
        for line in self:
            user_ids = line.student_ids.mapped("user_id").ids
            self.student_user_ids = [(6, 0, user_ids)]

    def _compute_domain_set_field(self):
        for rec in self:
            if rec.domain_set_field:
                rec.domain_set_field = False
            else:
                rec.domain_set_field = True

    @api.depends("course_id")
    def _compute_subject_domain(self):
        for line in self:
            subject_ids = []
            student_ids = []
            if line.course_id.id:
                subjects = self.env["xe.subject"].search(
                    [("course_ids", "in", line.course_id.id)]
                )
                for sub in subjects:
                    subject_ids.append(sub.id)
                for s in line.course_id.course_subject_line_ids:
                    subject_ids.append(s.id)
                subject_ids = list(set(subject_ids))
                # Student Value set based on the course field
                if line.classroom_id.id:
                    students = self.env["xe.student"].search(
                        [
                            ("course_id", "=", line.course_id.id),
                            ("classroom_id", "=", line.classroom_id.id),
                        ]
                    )
                else:
                    students = self.env["xe.student"].search(
                        [("course_id", "=", line.course_id.id)]
                    )
                for r in students:
                    student_ids.append(r.id)

                if subject_ids:
                    line.assigned_sub_ids = [(6, 0, subject_ids)]
                else:
                    line.assigned_sub_ids = False
                if student_ids:
                    line.assigned_stud_ids = [(6, 0, student_ids)]
                else:
                    line.assigned_stud_ids = False
            else:
                line.assigned_sub_ids = False
                line.assigned_stud_ids = False

    @api.onchange("classroom_id")
    def _onchange_student(self):
        student_ids = []
        for line in self:
            if line.course_id.id:
                if line.classroom_id.id:
                    students = self.env["xe.student"].search(
                        [
                            ("course_id", "=", line.course_id.id),
                            ("classroom_id", "=", line.classroom_id.id),
                        ]
                    )
                else:
                    students = self.env["xe.student"].search(
                        [("course_id", "=", line.course_id.id)]
                    )
                for r in students:
                    student_ids.append(r.id)

                if student_ids:
                    line.assigned_stud_ids = [(6, 0, student_ids)]

            else:
                line.assigned_stud_ids = False

    def assign(self):
        if not self.student_ids:
            raise UserError(
                _(
                    "You have not selected student(s), please select students under the allocation tab!"
                )
            )

        self.state = "assigned"
        if self.number == "New":
            self.number = self.env["ir.sequence"].next_by_code(
                "xe.assignment.seq"
            ) or _("New")
        msg = "Assigned by " + self.create_teacher_id.name
        self.message_post(
            body=msg,
            message_type="notification",
            email_from=self.env.user.login,
            author_id=self.env.user.partner_id.id,
            partner_ids=[self.env.user.partner_id.id],
        )

    def cancel(self):
        self.state = "cancel"

    def reset_to_draft(self):
        self.state = "draft"

    def submit_assignment(self):
        # student_id = (
        #     self.env["xe.student"].search([("user_id", "=", self.env.user.id)]).id
        # )
        student_id = self.student_ids[0].id
        assigned_stud_ids = []
        if self.env.user.has_group("xenesis_school_base.group_xe_parent"):
            parent_id = self.env["xe.parent"].search(
                [("user_id", "=", self.env.user.id)]
            )
            if parent_id:
                student_ids = parent_id.student_ids.filtered(
                    lambda l: l.classroom_id.id == self.classroom_id.id
                )
                for student in student_ids:
                    if student.id in self.mapped("student_ids").ids:
                        assigned_stud_ids.append(student.id)
        if self.env.user.has_group("xenesis_school_base.group_xe_staff"):
            assigned_stud_ids = (
                self.mapped("student_ids") and self.mapped("student_ids").ids
            )
        return {
            "name": _("Submit Assignment"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_model": "xe.assignment.submission",
            "context": {
                "default_assignment_id": self.id,
                "default_student_id": student_id,
                "default_assigned_student_ids": [(6, 0, assigned_stud_ids)],
            },
            "target": "current",
        }

    def _set_assignment_as_done(self):
        today = datetime.now()
        assignments = self.env["xe.assignment"].search([("state", "=", "assigned")])
        for obj in assignments:
            submit_date = obj.submit_date
            if (
                today.day == submit_date.day
                and today.month == submit_date.month
                and today.year == submit_date.year
                and today.hour == submit_date.hour
            ):
                obj.write({"state": "done"})

    def assignment_as_done(self):
        self.write({"state": "done"})

    @api.model
    def create(self, values):
        if not values.get("teacher_id"):
            values["teacher_id"] = (
                self.env["hr.employee"].search([("user_id", "=", self.env.user.id)]).id
            )
        result = super(Assignments, self).create(values)
        return result

    def view_submissions(self):
        action = {
            "name": _("Assignment Submissions"),
            "type": "ir.actions.act_window",
            "res_model": "xe.assignment.submission",
            "target": "current",
        }
        s_records = (
            self.env["xe.assignment.submission"]
            .search(
                [
                    ("assignment_id", "=", self.id),
                    ("state", "not in", ["draft", "cancel"]),
                ]
            )
            .ids
        )
        action["view_mode"] = "tree,form"
        action["domain"] = [("id", "in", s_records)]
        return action

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super(Assignments, self).get_view(view_id, view_type, **options)
        if self.env.user.has_group(
            "xenesis_school_base.group_xe_admin"
        ) or self.env.user.has_group("xenesis_school_base.group_xe_staff"):
            if view_type == "tree":
                doc = etree.XML(res["arch"])
                nodes = doc.xpath("//tree")
                for node in nodes:
                    node.set("create", "1")
                    node.set("edit", "1")
                res["arch"] = etree.tostring(doc)
            if view_type == "form":
                doc = etree.XML(res["arch"])
                nodes = doc.xpath("//form")
                for node in nodes:
                    node.set("create", "1")
                    node.set("edit", "1")
                res["arch"] = etree.tostring(doc)
        elif self.env.user.has_group("xenesis_school_base.group_xe_parent"):
            if view_type == "tree":
                doc = etree.XML(res["arch"])
                nodes = doc.xpath("//tree")
                for node in nodes:
                    node.set("create", "0")
                    node.set("edit", "0")
                res["arch"] = etree.tostring(doc)
            if view_type == "form":
                doc = etree.XML(res["arch"])
                nodes = doc.xpath("//form")
                for node in nodes:
                    node.set("create", "0")
                    node.set("edit", "0")
                res["arch"] = etree.tostring(doc)
        return res
