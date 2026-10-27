# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SubjectRegistration(models.Model):
    _name = "xe.subject.registration"
    _inherit = ["mail.thread"]
    _description = "Subject Registration"

    name = fields.Char("Number", tracking=True)
    student_id = fields.Many2one("xe.student", "Student")
    course_id = fields.Many2one("xe.course", "Class")
    create_user_id = fields.Many2one("res.users", default=lambda self: self.env.user.id)
    roll_number = fields.Char("Admission Number", related="student_id.roll_number")
    subject_ids = fields.Many2many("xe.subject", string="Subjects")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("approve", "Approve"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        tracking=True,
    )

    @api.constrains("course_id", "subject_ids")
    def check_subject_register(self):
        if self.course_id and not self.course_id.is_attendance_subject_wise:
            raise UserError(
                _("Sorry !! Your Course is not configured for Subject Registration")
            )
        if (
            self.subject_ids
            and len(self.subject_ids) > self.course_id.max_subject_registration
        ):
            raise UserError(_("Maximum Number of subject registration exceeds "))

    @api.onchange("create_user_id")
    def set_student(self):
        for record in self:
            if record.create_user_id:
                student_obj = self.env["xe.student"].search(
                    [("user_id", "=", record.create_user_id.id)]
                )
                if student_obj:
                    record.student_id = student_obj.id
                    record.course_id = student_obj.course_id.id

    @api.model
    def create(self, vals):
        """Create new Sequence"""
        if vals.get("name", "New") == "New":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("sub.registration.seq") or "New"
            )
        result = super(SubjectRegistration, self).create(vals)
        return result

    def action_submit(self):
        self.state = "submit"

    def action_approve(self):
        mandatory_subs = []
        elective_subs = []
        for sub in self.subject_ids:
            if sub.subject_mode == "yes":
                elective_subs.append(sub.id)
            else:
                mandatory_subs.append(sub.id)
        write_vals = {}
        if elective_subs:
            write_vals["elective_subjects_ids"] = [(6, 0, elective_subs)]
        if mandatory_subs:
            write_vals["mandatory_subjects_ids"] = [(6, 0, mandatory_subs)]
        self.student_id.write(write_vals)
        self.state = "approve"

    def action_cancel(self):
        self.state = "cancel"

    def reset_to_draft(self):
        self.state = "draft"
