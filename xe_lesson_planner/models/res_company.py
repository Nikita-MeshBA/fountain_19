# Copyright 2011, 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    reg_no = fields.Char(string="Register No")
    report_watermark = fields.Image()


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def scheme_of_work_view(self):
        form_view = self.env.ref("xe_lesson_planner.view_scheme_of_work_form")
        tree_view = self.env.ref("xe_lesson_planner.view_scheme_of_work_tree")
        scheme_of_work_ids = (
            self.env["scheme.of.work"]
            .search([("employee_id", "=", self.id), ("status", "=", "approved")])
            .ids
        )
        value = {
            "domain": str([("id", "in", scheme_of_work_ids)]),
            "view_type": "form",
            "view_mode": "tree, form",
            "res_model": "scheme.of.work",
            "view_id": False,
            "views": [
                (tree_view and tree_view.id or False, "tree"),
                (form_view and form_view.id or False, "form"),
            ],
            "type": "ir.actions.act_window",
            "res_ids": scheme_of_work_ids,
            "target": "current",
        }
        return value

    def lesson_planner_view(self):
        form_view = self.env.ref("xe_lesson_planner.view_lesson_plan_form")
        tree_view = self.env.ref("xe_lesson_planner.view_lesson_plan_tree")
        scheme_of_work_ids = (
            self.env["lesson.plan"]
            .search([("employee_id", "=", self.id), ("status", "=", "approved")])
            .ids
        )
        value = {
            "domain": str([("id", "in", scheme_of_work_ids)]),
            "view_type": "form",
            "view_mode": "tree, form",
            "res_model": "lesson.plan",
            "view_id": False,
            "views": [
                (tree_view and tree_view.id or False, "tree"),
                (form_view and form_view.id or False, "form"),
            ],
            "type": "ir.actions.act_window",
            "res_ids": scheme_of_work_ids,
            "target": "current",
        }
        return value


class HrEmployeeApproval(models.Model):
    _name = "hr.employee.approval"
    _rec_name = "type"
    _description = "Employee Approval"

    type = fields.Selection(
        selection=[("scheme", "Scheme Of Work"), ("lesson_plan", "Lesson Plan")],
    )
    employee_id = fields.Many2one("hr.employee")
    # old field
    department_head = fields.Many2one("hr.employee")
    # new field
    department_head_id = fields.Many2one("hr.employee")
    # old field
    head_teacher = fields.Many2one("hr.employee")
    # new field
    head_teacher_id = fields.Many2one("hr.employee")
    first_approval = fields.Boolean()
    first_approval_confirm = fields.Boolean()
    first_approval_date = fields.Date()
    # old field
    first_approval_user = fields.Many2one("res.users")
    # new field
    first_approval_user_id = fields.Many2one("res.users")
    scheme_of_work_id = fields.Many2one("scheme.of.work")
    seq_name = fields.Char(related="scheme_of_work_id.seq_name")
    lesson_plan_id = fields.Many2one("lesson.plan")
    seq_name_lp = fields.Char(related="lesson_plan_id.seq_name_lp")
    first_status = fields.Selection(
        selection=[
            ("first_approval", "Waiting For First Approval"),
            ("first_approval_confirmed", "Approved"),
        ],
        string="Status",
        default="first_approval",
    )
    second_approval = fields.Boolean()
    second_approval_confirm = fields.Boolean()
    second_approval_date = fields.Date()
    # old field
    second_approval_user = fields.Many2one("res.users")
    # new field
    second_approval_user_id = fields.Many2one("res.users")
    second_status = fields.Selection(
        selection=[
            ("second_approval", "Waiting For Second Approval"),
            ("second_approval_confirmed", "Approved"),
        ],
        string="Status",
        default="second_approval",
    )

    def first_approval_method(self):
        scheme_of_work_rec = (
            self.env["scheme.of.work"].sudo().browse(self.scheme_of_work_id.id)
        )

        self.first_approval_confirm = True
        self.first_status = "first_approval_confirmed"

        if scheme_of_work_rec:
            head_teacher_id = scheme_of_work_rec.head_teacher_id
            if head_teacher_id.user_id:
                user_id = head_teacher_id.user_id.id
            else:
                if head_teacher_id:
                    head_teacher_id.sudo().create_user()
                    user_id = head_teacher_id.user_id.id

            self.env["hr.employee.approval"].sudo().create(
                {
                    "second_approval": True,
                    "second_approval_user_id": user_id,
                    "second_approval_date": fields.Date.today(),
                    "scheme_of_work_id": self.scheme_of_work_id.id,
                    "head_teacher_id": head_teacher_id.id,
                    "type": self.type,
                }
            )

        lesson_plan_rec = self.env["lesson.plan"].sudo().browse(self.lesson_plan_id.id)
        if lesson_plan_rec:
            head_teacher_id = lesson_plan_rec.head_teacher_id
            if head_teacher_id.user_id:
                user_id = head_teacher_id.user_id.id
            else:
                head_teacher_id.create_user()
                user_id = head_teacher_id.user_id.id

            self.env["hr.employee.approval"].sudo().create(
                {
                    "second_approval": True,
                    "second_approval_user_id": user_id,
                    "second_approval_date": fields.Date.today(),
                    "scheme_of_work_id": self.scheme_of_work_id.id,
                    "lesson_plan_id": self.lesson_plan_id.id,
                    "head_teacher_id": head_teacher_id.id,
                    "type": self.type,
                }
            )

        return True

    def second_approval_method(self):
        if self.scheme_of_work_id:
            scheme_of_work_rec = (
                self.env["scheme.of.work"].sudo().browse(self.scheme_of_work_id.id)
            )
            scheme_of_work_rec.sudo().write({"status": "approved"})
            self.second_approval_confirm = True
            self.second_status = "second_approval_confirmed"

        if self.lesson_plan_id:
            lesson_plan_rec = (
                self.env["lesson.plan"].sudo().browse(self.lesson_plan_id.id)
            )
            lesson_plan_rec.sudo().write({"status": "approved"})
            self.second_approval_confirm = True
            self.second_status = "second_approval_confirmed"


class HrEmployeeApprovalCBC(models.Model):
    _name = "hr.employee.approval.cbc"
    _rec_name = "type"
    _description = "Employee Approval CBC"

    type = fields.Selection(
        selection=[
            ("scheme", "CBC Scheme Of Work"),
            ("lesson_plan", "CBC Lesson Plan"),
        ],
    )
    employee_id = fields.Many2one("hr.employee")
    # old field
    department_head = fields.Many2one("hr.employee")
    # new field
    department_head_id = fields.Many2one("hr.employee")
    # old field
    head_teacher = fields.Many2one("hr.employee")
    # new field
    head_teacher_id = fields.Many2one("hr.employee")
    first_approval = fields.Boolean()
    first_approval_confirm = fields.Boolean()
    first_approval_date = fields.Date()
    # old field
    first_approval_user = fields.Many2one("res.users")
    # new field
    first_approval_user_id = fields.Many2one("res.users")
    cbc_scheme_of_work_id = fields.Many2one("cbc.scheme.of.work")
    seq_name = fields.Char(related="cbc_scheme_of_work_id.seq_name")
    cbc_lesson_plan_id = fields.Many2one("cbc.lesson.plan")
    seq_name_lp = fields.Char(related="cbc_lesson_plan_id.seq_name_lp")
    first_status = fields.Selection(
        selection=[
            ("first_approval", "Waiting For First Approval"),
            ("first_approval_confirmed", "Approved"),
        ],
        string="Status",
        default="first_approval",
    )
    second_approval = fields.Boolean()
    second_approval_confirm = fields.Boolean()
    second_approval_date = fields.Date()
    # old field
    second_approval_user = fields.Many2one("res.users")
    # new field
    second_approval_user_id = fields.Many2one("res.users")
    second_status = fields.Selection(
        selection=[
            ("second_approval", "Waiting For Second Approval"),
            ("second_approval_confirmed", "Approved"),
        ],
        string="Status",
        default="second_approval",
    )

    def first_approval_method(self):
        scheme_of_work_rec = (
            self.env["cbc.scheme.of.work"].sudo().browse(self.cbc_scheme_of_work_id.id)
        )
        self.first_approval_confirm = True
        self.first_status = "first_approval_confirmed"

        if scheme_of_work_rec:
            head_teacher_id = scheme_of_work_rec.head_teacher_id
            if head_teacher_id.user_id:
                user_id = head_teacher_id.user_id.id
            else:
                if head_teacher_id:
                    head_teacher_id.sudo().create_user()
                    user_id = head_teacher_id.user_id.id

            self.env["hr.employee.approval.cbc"].sudo().create(
                {
                    "second_approval": True,
                    "second_approval_user_id": user_id,
                    "second_approval_date": fields.Date.today(),
                    "cbc_scheme_of_work_id": self.cbc_scheme_of_work_id.id,
                    "head_teacher_id": head_teacher_id.id,
                    "type": self.type,
                }
            )

        lesson_plan_rec = (
            self.env["cbc.lesson.plan"].sudo().browse(self.cbc_lesson_plan_id.id)
        )
        if lesson_plan_rec:
            head_teacher_id = lesson_plan_rec.head_teacher_id
            if head_teacher_id.user_id:
                user_id = head_teacher_id.user_id.id
            else:
                head_teacher_id.create_user()
                user_id = head_teacher_id.user_id.id

            self.env["hr.employee.approval.cbc"].sudo().create(
                {
                    "second_approval": True,
                    "second_approval_user_id": user_id,
                    "second_approval_date": fields.Date.today(),
                    "cbc_lesson_plan_id": self.cbc_lesson_plan_id.id,
                    "head_teacher_id": head_teacher_id.id,
                    "type": self.type,
                }
            )

        return True

    def second_approval_method(self):
        if self.cbc_scheme_of_work_id:
            scheme_of_work_rec = (
                self.env["cbc.scheme.of.work"]
                .sudo()
                .browse(self.cbc_scheme_of_work_id.id)
            )
            scheme_of_work_rec.sudo().write({"status": "approved"})
            self.second_approval_confirm = True
            self.second_status = "second_approval_confirmed"

        if self.cbc_lesson_plan_id:
            lesson_plan_rec = (
                self.env["cbc.lesson.plan"].sudo().browse(self.cbc_lesson_plan_id.id)
            )
            lesson_plan_rec.sudo().write({"status": "approved"})
            self.second_approval_confirm = True
            self.second_status = "second_approval_confirmed"


class LessonPlannerTiming(models.Model):
    _name = "lesson.planner.timing"

    name = fields.Char()
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    duration = fields.Char(compute="_compute_duration")

    @api.constrains("start_time", "end_time")
    def _check_timing(self):
        for record in self:
            if record.start_time > record.end_time:
                raise ValidationError(
                    _("End time should geater than Start time...")
                )

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                days_str = ""
                time_diff = rec.end_time - rec.start_time
                if time_diff:
                    seconds = time_diff.days * 24 * 3600 + time_diff.seconds
                    minutes, seconds = divmod(seconds, 60)
                    hours, minutes = divmod(minutes, 60)
                    days, hours = divmod(hours, 24)
                    if days:
                        days_str += "%d Days" % (days)
                    if hours:
                        days_str += " %d Hours" % (hours)
                    if minutes:
                        days_str += " %d Minutes" % (minutes)
                    if seconds:
                        days_str += " %d Seconds" % (seconds)
                rec.duration = days_str
            else:
                rec.duration = ""
