import datetime
from lxml import etree
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class AssignmentSubmission(models.Model):
    _name = "xe.assignment.submission"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Assignment Submission"

    @api.model
    def _get_student_id(self):
        for line in self:
            if line.create_student_id:
                student_id = (
                    self.env["xe.student"]
                    .search([("user_id", "=", line.create_teacher_id.id)])
                    .id
                )
                if student_id:
                    return student_id

    name = fields.Char(default="New")
    student_id = fields.Many2one("xe.student", default=_get_student_id, tracking=True)
    assignment_id = fields.Many2one("xe.assignment", tracking=True)
    submit_date = fields.Datetime("Submission Date", tracking=True)
    description = fields.Text(tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("change_request", "Change Request"),
            ("late_submit", "Late Submitted"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        tracking=True,
    )
    notes = fields.Text("Notes By Teacher")
    marks_on_submit = fields.Float("Marks", tracking=True)
    create_student_id = fields.Many2one("res.users", string="Users")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    assigned_student_ids = fields.Many2many("xe.student")

    @api.onchange("assignment_id")
    def _onchange_assignment_id(self):
        for rec in self:
            assigned_stud_ids = []
            if (
                rec.env.user.has_group("xenesis_school_base.group_xe_parent")
                and rec.assignment_id
            ):
                parent_id = self.env["xe.parent"].search(
                    [("user_id", "=", self.env.user.id)]
                )
                if parent_id:
                    student_ids = parent_id.student_ids.filtered(
                        lambda l: l.classroom_id.id == rec.assignment_id.classroom_id.id
                    )
                    for student in student_ids:
                        if student.id in rec.assignment_id.mapped("student_ids").ids:
                            assigned_stud_ids.append(student.id)
            if (
                self.env.user.has_group("xenesis_school_base.group_xe_staff")
                and rec.assignment_id
            ):
                assigned_stud_ids = rec.assignment_id.student_ids.ids
            rec.assigned_student_ids = [(6, 0, assigned_stud_ids)]

    @api.constrains("marks_on_submit")
    def _check_given_marks(self):
        if self.marks_on_submit > self.assignment_id.total_marks:
            raise UserError(
                _(
                    "Marks can not exceed the Assignment Total Marks "
                    + str(self.assignment_id.total_marks)
                )
            )

    def submit(self):
        assignment_id = (
            self.env["xe.assignment"].sudo().browse(int(self.assignment_id.id))
        )
        if assignment_id.submit_date < datetime.datetime.today():
            name = self.env["ir.sequence"].next_by_code("xe.assignmentsubmit.seq") or _(
                "New"
            )
            submit_date = datetime.datetime.today()
            self.sudo().write(
                {"state": "late_submit", "name": name, "submit_date": submit_date}
            )
        else:
            name = self.env["ir.sequence"].next_by_code("xe.assignmentsubmit.seq") or _(
                "New"
            )
            submit_date = datetime.datetime.today()
            self.sudo().write(
                {"state": "submitted", "name": name, "submit_date": submit_date}
            )

    def change_request(self):
        self.sudo().state = "change_request"

    @api.model
    def create(self, values):
        if "student_id" not in values:
            values["student_id"] = (
                self.env["xe.student"].search([("user_id", "=", self.env.user.id)]).id
            )
        result = super(AssignmentSubmission, self).create(values)
        return result

    def accept(self):
        self.sudo().state = "accepted"

    def cancel(self):
        self.sudo().state = "cancel"

    def reset_to_draft(self):
        self.sudo().state = "draft"

    def reject(self):
        self.sudo().state = "rejected"

    @api.model
    def assignment_submit_act(self):
        action = {
            "name": _("Assignment Submissions"),
            "view_mode": "tree,form",
            "res_model": "xe.assignment.submission",
            "type": "ir.actions.act_window",
        }
        return action

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super(AssignmentSubmission, self).get_view(view_id, view_type, **options)
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
                description_fields = doc.xpath("//field[@name='description']")[0].set(
                    "readonly", "0"
                )
                marks_fields = doc.xpath("//field[@name='marks_on_submit']")[0].set(
                    "readonly", "0"
                )
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
                # nodes = doc.xpath("//form")
                # for node in nodes:
                #     node.set("create", "0")
                #     node.set("edit", "0")
                description_fields = doc.xpath("//field[@name='description']")[0].set(
                    "readonly", "1"
                )
                marks_fields = doc.xpath("//field[@name='marks_on_submit']")[0].set(
                    "readonly", "1"
                )
                res["arch"] = etree.tostring(doc)
        return res
