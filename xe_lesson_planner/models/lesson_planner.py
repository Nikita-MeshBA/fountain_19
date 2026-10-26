from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SchemeOfWork(models.Model):
    _name = "scheme.of.work"
    _description = "Scheme of Work"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "employee_id"

    def _default_employee_id(self):
        employee_rec = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.user.id)], limit=1)
        )
        return employee_rec.id

    def _default_department_head_id(self):
        return self.employee_id.parent_id.id

    def _default_head_teacher(self):
        return self.employee_id.parent_id.id

    def _default_year(self):
        current_date = fields.date.today()
        academic_record = (
            self.env["xe.academic.year"]
            .sudo()
            .search(
                [("start_date", "<=", current_date), ("end_date", ">=", current_date)],
                limit=1,
            )
        )
        return academic_record.id

    is_scheme_of_work = fields.Boolean()
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("waiting_for_approval", "Waiting for approval"),
            ("1st_approval", "1st aprroval"),
            ("2nd_approval", "2nd approval"),
        ],
        default="draft",
        tracking=True,
    )
    seq_name = fields.Char(readonly=True)
    employee_id = fields.Many2one(
        "hr.employee", string="Name", required=True, default=_default_employee_id
    )
    # old field
    department_head = fields.Many2one("hr.employee", default=_default_department_head_id)
    # new field
    department_head_id = fields.Many2one("hr.employee", default=_default_department_head_id)
    department_id = fields.Many2one(related="department_head_id.department_id")
    department_manager_id = fields.Many2one(
        related="department_head_id.department_id.manager_id"
    )
    # new field
    head_teacher = fields.Many2one("hr.employee", default=_default_head_teacher)
    # old field
    head_teacher_id = fields.Many2one("hr.employee", default=_default_head_teacher)
    company_id = fields.Many2one(
        "res.company", string="School", default=lambda self: self.env.company
    )
    reg_no = fields.Char(related="company_id.reg_no")
    period_per_week = fields.Integer()
    type_select = fields.Selection(
        selection=[
            ("class", "Class"),
            ("both", "Both"),
        ],
        string="Form",
        default="class",
    )
    class_id = fields.Many2one("xe.course", string="Class")
    classroom_id = fields.Many2one("xe.classroom", string="Class Room")
    # old field
    year = fields.Many2one("xe.academic.year", default=_default_year)
    # new field
    year_id = fields.Many2one("xe.academic.year", default=_default_year)
    # old field
    term = fields.Many2one("xe.academic.terms")
    # new field
    term_id = fields.Many2one("xe.academic.terms")
    scheme_of_work_ids = fields.One2many("scheme.of.work.line", "scheme_of_work_id")
    is_submit = fields.Boolean()
    is_resubmit = fields.Boolean()
    assigned_sub_ids = fields.Many2many(
        "xe.subject",
        "dummy_subj_rel",
        "assignment_id",
        "sub_id",
        string="Assigned Subjects",
    )

    @api.onchange("class_id")
    def assigned_sub_ids_onchange(self):
        for line in self:
            subject_ids = []
            if line.class_id.id:
                # Subject value set based on the course field
                for s in line.class_id.course_subject_line_ids:
                    subject_ids.append(s.id)
                return {"domain": {"assigned_sub_ids": [("id", "in", subject_ids)]}}
            else:
                return {"domain": {"assigned_sub_ids": [("id", "in", [])]}}

    @api.depends("class_id")
    def _subject_domain(self):
        for line in self:
            subject_ids = []
            if line.class_id.id:
                # Subject value set based on the course field
                for s in line.class_id.course_subject_line_ids:
                    subject_ids.append(s.id)

                if subject_ids:
                    line.assigned_sub_ids = [(6, 0, subject_ids)]
                else:
                    line.assigned_sub_ids = False
            else:
                line.assigned_sub_ids = False

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_head_id = self.employee_id.parent_id.id
            self.head_teacher_id = self.employee_id.parent_id.id

    def first_approval(self):
        if self.department_head_id:
            if self.department_head_id.user_id:
                user_id = self.department_head_id.user_id.id
            else:
                self.department_head_id.create_user()
                user_id = self.department_head_id.user_id.id

            self.env["hr.employee.approval"].sudo().create(
                {
                    "first_approval": True,
                    "first_approval_date": fields.Date.today(),
                    "first_approval_user_id": user_id,
                    "scheme_of_work_id": self.id,
                    "employee_id": self.employee_id.id,
                    "department_head_id": self.department_head_id.id,
                    "type": "scheme",
                }
            )
            return self.write({"status": "waiting_approval"})
        else:
            raise ValidationError(
                _("Please update the Employee Profile Manager Field Value...")
            )

    def reset_draft(self):
        self.status = "draft"

    @api.model
    def create(self, vals):
        if vals:
            vals["seq_name"] = (
                self.env["ir.sequence"].next_by_code("scheme.of.work") or "/"
            )
            vals["is_scheme_of_work"] = True
            lesson_plan_user = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_user"
            )
            lesson_plan_admin = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_manager"
            )
            if lesson_plan_user and lesson_plan_admin == False:
                vals["is_submit"] = True
        result = super(SchemeOfWork, self).create(vals)
        return result

    def write(self, vals):
        if vals:
            lesson_plan_user = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_user"
            )
            lesson_plan_admin = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_manager"
            )
            if lesson_plan_admin or lesson_plan_user:
                vals["is_scheme_of_work"] = True
        result = super(SchemeOfWork, self).write(vals)
        return result

    def button_submit(self):
        self.status = "waiting_for_approval"

    def button_first_approval(self):
        self.status = "1st_approval"

    def button_second_approval(self):
        self.status = "2nd_approval"


class SchemeOfWorkLine(models.Model):
    _name = "scheme.of.work.line"
    _description = "Scheme of Work Line"

    week = fields.Integer()
    lesson = fields.Char()
    topic = fields.Char()
    sub_topic = fields.Char()
    objectives = fields.Text()
    key_inquiry_questions = fields.Text()
    assessment_methods = fields.Text()
    learning_activities = fields.Char()
    learning_resources = fields.Char()
    remarks = fields.Text()
    scheme_of_work_id = fields.Many2one("scheme.of.work")


class LessonPlan(models.Model):
    _name = "lesson.plan"
    _description = "Lesson Plan"
    _rec_name = "employee_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_head_branch(self):
        employee_rec = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.user.id)], limit=1)
        )
        return employee_rec.id

    def _default_department_head_id(self):
        return self.employee_id.parent_id.id

    def _default_head_teacher(self):
        return self.employee_id.parent_id.id

    def _default_year(self):
        current_date = fields.date.today()
        academic_record = (
            self.env["xe.academic.year"]
            .sudo()
            .search(
                [("start_date", "<=", current_date), ("end_date", ">=", current_date)],
                limit=1,
            )
        )
        return academic_record.id

    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("waiting_for_approval", "Waiting for approval"),
            ("1st_approval", "1st aprroval"),
            ("2nd_approval", "2nd approval"),
        ],
        default="draft",
        tracking=True,
    )
    seq_name_lp = fields.Char(readonly=True)
    employee_id = fields.Many2one("hr.employee", default=_default_head_branch)
    # old field
    department_head = fields.Many2one("hr.employee", default=_default_department_head_id)
    # new field
    department_head_id = fields.Many2one("hr.employee", default=_default_department_head_id)
    # old field
    head_teacher = fields.Many2one("hr.employee", default=_default_head_teacher)
    # new field
    head_teacher_id = fields.Many2one("hr.employee", default=_default_head_teacher)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    reg_no = fields.Char(related="company_id.reg_no")
    week = fields.Integer()
    class_id = fields.Many2one("xe.course", string="Class")
    classroom_id = fields.Many2one("xe.classroom", string="Class Room")
    no_of_students = fields.Integer(compute="_compute_no_of_student")
    # old field
    subject = fields.Many2one("xe.subject")
    # new field
    subject_id = fields.Many2one("xe.subject")
    lesson = fields.Char()
    topic = fields.Char()
    sub_topic = fields.Char()
    lesson_date = fields.Datetime()
    lesson_plan_ids = fields.One2many("lesson.plan.line", "lesson_plan_id")
    scheme_of_work_id = fields.Many2one("scheme.of.work.line")
    is_lesson_plan = fields.Boolean()
    is_submit = fields.Boolean()
    is_resubmit = fields.Boolean()
    academic_year_id = fields.Many2one("xe.academic.year", default=_default_year)
    academic_term_id = fields.Many2one("xe.academic.terms")

    @api.depends("classroom_id")
    def _compute_no_of_student(self):
        for rec in self:
            rec.no_of_students = 0
            if rec.classroom_id:
                students = self.env["xe.student"].search_count([("classroom_id", "=", rec.classroom_id.id)])
                if students:
                    rec.no_of_students = students

    @api.model
    def create(self, vals):
        if vals:
            vals["seq_name_lp"] = (
                self.env["ir.sequence"].next_by_code("lesson.plan") or "/"
            )
            vals["is_lesson_plan"] = True
            lesson_plan_user = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_user"
            )
            lesson_plan_admin = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_manager"
            )
            if lesson_plan_user and lesson_plan_admin == False:
                vals["is_submit"] = True
        result = super(LessonPlan, self).create(vals)
        return result

    def write(self, vals):
        if vals:
            lesson_plan_user = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_user"
            )
            lesson_plan_admin = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_manager"
            )
            if lesson_plan_admin or lesson_plan_user:
                vals["is_lesson_plan"] = True
        result = super(LessonPlan, self).write(vals)
        return result

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_head_id = self.employee_id.parent_id.id
            self.head_teacher_id = self.employee_id.parent_id.id

    def first_approval(self):
        if self.department_head_id:
            if self.department_head_id.user_id:
                user_id = self.department_head_id.user_id.id
            else:
                self.department_head_id.create_user()
                user_id = self.department_head_id.user_id.id

            self.env["hr.employee.approval"].sudo().create(
                {
                    "first_approval": True,
                    "lesson_plan_id": self.id,
                    "first_approval_date": fields.Date.today(),
                    "first_approval_user_id": user_id,
                    "employee_id": self.employee_id.id,
                    "department_head_id": self.department_head_id.id,
                    "type": "lesson_plan",
                }
            )
            return self.write({"status": "waiting_approval"})
        else:
            raise ValidationError(
                _("Please update the Employee Profile Manager Field Value...")
            )

    def button_submit(self):
        self.status = "waiting_for_approval"

    def button_first_approval(self):
        self.status = "1st_approval"

    def button_second_approval(self):
        self.status = "2nd_approval"

    def reset_draft(self):
        self.status = "draft"

class LessonPlanLine(models.Model):
    _name = "lesson.plan.line"
    _description = "Lesson Plan Line"
    _rec_name = "content"

    time = fields.Char()
    content = fields.Text()
    learning_activities = fields.Text()
    learning_resources = fields.Text()
    lesson_plan_id = fields.Many2one("lesson.plan")
