from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_department_head_approval = fields.Boolean(string="Departmental Head Approval")
    is_head_teacher_approval = fields.Boolean(string="Head Teacher Approval")

class CBCSchemeOfWork(models.Model):
    _name = "cbc.scheme.of.work"
    _description = "CBC Scheme of Work"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "employee_id"

    def _default_employee_id(self):
        employee_rec = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.user.id),("company_id",'=',self.env.company.id)], limit=1)
        )
        return employee_rec.id

    def _compute_department_head_ids(self):
        employee_ids = self.env['hr.employee'].sudo().search([('is_department_head_approval','=',True)])
        return employee_ids.ids

    def _compute_head_teacher_ids(self):
        employee_ids = self.env['hr.employee'].sudo().search([('is_head_teacher_approval','=',True)])
        return employee_ids.ids

    def _default_department_head(self):
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
            ("approved", "Approved"),
            ("rejected", "Rejected")
        ],
        default="draft",
        tracking=True,
    )
    seq_name = fields.Char(readonly=True)
    employee_id = fields.Many2one(
        "hr.employee", string="Name", required=True, default=_default_employee_id
    )
    # old field
    department_head = fields.Many2one("hr.employee", default=_default_department_head,
                                      domain="[('id', 'in', department_head_ids)]")
    # new field
    department_head_id = fields.Many2one("hr.employee", default=_default_department_head,
                                         domain="[('id', 'in', department_head_ids)]")
    department_id = fields.Many2one(related="department_head_id.department_id")
    department_head_ids = fields.Many2many('hr.employee', 'department_head_cbc_rel', 'did', 'cid',
                                           default=_compute_department_head_ids)
    department_manager_id = fields.Many2one(
        related="department_head_id.department_id.manager_id"
    )
    # old field
    head_teacher = fields.Many2one("hr.employee", default=_default_head_teacher,
                                   domain="[('id', 'in', head_teacher_ids)]")
    # new field
    head_teacher_id = fields.Many2one("hr.employee", default=_default_head_teacher,
                                      domain="[('id', 'in', head_teacher_ids)]")
    head_teacher_ids = fields.Many2many('hr.employee','head_teacher_cbc_rel','tid','cbid',
        default=_compute_head_teacher_ids)

    company_id = fields.Many2one(
        "res.company", string="School", default=lambda self: self.env.company
    )
    reg_no = fields.Char(related="employee_id.registration_number")
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
    cbc_scheme_of_work_ids = fields.One2many(
        "cbc.scheme.of.work.line", "cbc_scheme_of_work_id"
    )
    tsc_number = fields.Char(related="employee_id.tsc_no")
    is_submit = fields.Boolean()
    is_resubmit = fields.Boolean()
    assigned_sub_ids = fields.Many2many(
        "xe.subject",
        "sbc_subj_rel",
        "assignment_id",
        "sub_id",
        string="Assigned Subjects",
    )
    is_manager = fields.Boolean(compute="_is_manager",default=False)
    is_approver =  fields.Boolean(compute="_is_approver",default=False)
    is_ht_approver =  fields.Boolean(compute="_is_ht_approver",default=False)

    def _is_approver(self):
        for rec in self:
            if rec.department_head:
                if rec.department_head.user_id.id == self.env.user.id:
                    rec.is_approver = True
                else:
                    rec.is_approver = False
            else:
                employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id),('company_id','=',self.env.company.id)],limit=1)
                if employee_id.is_department_head_approval:
                    rec.is_approver = True
                else:
                    rec.is_approver = False

    def _is_ht_approver(self):
        for rec in self:
            if rec.head_teacher:
                if rec.head_teacher.user_id.id == self.env.user.id:
                    rec.is_ht_approver = True
                else:
                    rec.is_ht_approver = False
            else:
                employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id),('company_id','=',self.env.company.id)],limit=1)
                if employee_id.is_head_teacher_approval:
                    rec.is_ht_approver = True
                else:
                    rec.is_ht_approver = False

    def _is_manager(self):
        for rec in self:
            if self.env.user.has_group("xe_lesson_planner.group_lesson_plan_manager") and rec.status in ("approved", "rejected"):
                rec.is_manager = True
            elif rec.status in ("departmental_approved", "head_teacher_approved"):
                rec.is_manager = True
            else:
                rec.is_manager = False

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

    def reset_draft(self):
        self.status = "draft"

    def first_approval(self):
        if self.department_head_id:
            if self.department_head_id.user_id:
                user_id = self.department_head_id.user_id.id
            else:
                self.department_head_id.create_user()
                user_id = self.department_head_id.user_id.id

            self.env["hr.employee.approval.cbc"].sudo().create(
                {
                    "first_approval": True,
                    "first_approval_date": fields.Date.today(),
                    "first_approval_user_id": user_id,
                    "cbc_scheme_of_work_id": self.id,
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

    @api.model
    def create(self, vals):
        if vals:
            x = self.env["ir.sequence"].next_by_code("cbc.scheme.of.work") or "/"
            vals["seq_name"] = x
            vals["is_scheme_of_work"] = True
            lesson_plan_user = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_user"
            )
            lesson_plan_admin = self.user_has_groups(
                "xe_lesson_planner.group_lesson_plan_manager"
            )
            if lesson_plan_user and lesson_plan_admin == False:
                vals["is_submit"] = True
        result = super(CBCSchemeOfWork, self).create(vals)
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
        result = super(CBCSchemeOfWork, self).write(vals)
        return result

    def button_submit(self):
        self.status = "waiting_for_approval"

    def button_first_approval(self):
        self.status = "1st_approval"

    def button_second_approval(self):
        self.status = "approved"

    def button_rejected(self):
        self.status = "rejected"

    def import_excel(self):
         return {
            "name": _("Import CBC Scheme Of Work Line"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "import.cbc.work.line",
            "target": "new",
        }

    def export_excel(self):
        data = {
            "ids": self.ids,
            "model": self._name,
        }
        return self.env.ref(
            "xe_lesson_planner.cbc_scheme_work_xlsx_report"
        ).report_action(self, data=data)

class CBCSchemeOfWorkLine(models.Model):
    _name = "cbc.scheme.of.work.line"
    _description = "CBC Scheme of Work Line"

    week = fields.Char()
    lesson = fields.Char()
    topic = fields.Text()
    sub_topic = fields.Text()
    objectives = fields.Text()
    key_inquiry_questions = fields.Text()
    assessment_methods = fields.Text()
    learning_activities = fields.Text()
    learning_resources = fields.Text()
    remarks = fields.Text()
    cbc_scheme_of_work_id = fields.Many2one("cbc.scheme.of.work")


class CBCLessonPlan(models.Model):
    _name = "cbc.lesson.plan"
    _description = "CBC Lesson Plan"
    _rec_name = "employee_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_head_branch(self):
        employee_rec = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.user.id),("company_id",'=',self.env.company.id)], limit=1)
        )
        return employee_rec.id

    def _default_department_head(self):
        return self.employee_id.parent_id.id

    def _default_head_teacher(self):
        return self.employee_id.parent_id.id

    def _compute_department_head_ids(self):
        employee_ids = self.env['hr.employee'].sudo().search([('is_department_head_approval','=',True)])
        return employee_ids.ids

    def _compute_head_teacher_ids(self):
        employee_ids = self.env['hr.employee'].sudo().search([('is_head_teacher_approval', '=', True)])
        return employee_ids.ids

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
            ("approved", "Approved"),
            ("rejected", "Rejected")
        ],
        default="draft",
        tracking=True,
    )
    age = fields.Text("Age")
    seq_name_lp = fields.Char(readonly=True)
    employee_id = fields.Many2one("hr.employee", default=_default_head_branch)
    # old field
    department_head = fields.Many2one("hr.employee", default=_default_department_head,
                                      domain="[('id','in',department_head_ids)]")
    # new field
    department_head_id = fields.Many2one("hr.employee", default=_default_department_head,
                                         domain="[('id','in',department_head_ids)]")
    # old field
    head_teacher = fields.Many2one("hr.employee", default=_default_head_teacher,
                                   domain="[('id','in',head_teacher_ids)]")
    # new field
    head_teacher_id = fields.Many2one("hr.employee", default=_default_head_teacher,
                                      domain="[('id','in',head_teacher_ids)]")
    department_head_ids = fields.Many2many('hr.employee', 'department_head_cbc_lesson_rel', 'did', 'cid',
                                           default=_compute_department_head_ids)
    head_teacher_ids = fields.Many2many('hr.employee', 'head_teacher_cbc_lesson_rel', 'tid', 'cbid',
                                        default=_compute_head_teacher_ids)

    is_approver = fields.Boolean(compute="_is_approver", default=False)
    is_ht_approver = fields.Boolean(compute="_is_ht_approver", default=False)

    academic_year_id = fields.Many2one("xe.academic.year", default=_default_year)
    academic_term_id = fields.Many2one("xe.academic.terms")
    learning_outcomes_ids = fields.One2many("specific.learning.outcomes", "lesson_plan_id")
    key_inquiry_questions_ids = fields.One2many("key.inquiry.questions", "lesson_plan_id")
    learning_resources_ids = fields.One2many("learning.resources", "lesson_plan_id")

    def _is_approver(self):
        for rec in self:
            if rec.department_head:
                if rec.department_head.user_id.id == self.env.user.id:
                    rec.is_approver = True
                else:
                    rec.is_approver = False
            else:
                employee_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', self.env.user.id), ('company_id', '=', self.env.company.id)], limit=1)
                if employee_id.is_department_head_approval:
                    rec.is_approver = True
                else:
                    rec.is_approver = False

    def _is_ht_approver(self):
        for rec in self:
            if rec.head_teacher:
                if rec.head_teacher.user_id.id == self.env.user.id:
                    rec.is_ht_approver = True
                else:
                    rec.is_ht_approver = False
            else:
                employee_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', self.env.user.id), ('company_id', '=', self.env.company.id)], limit=1)
                if employee_id.is_head_teacher_approval:
                    rec.is_ht_approver = True
                else:
                    rec.is_ht_approver = False

    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    reg_no = fields.Char(related="employee_id.registration_number")
    week = fields.Integer()
    class_id = fields.Many2one("xe.course", string="Class")
    classroom_id = fields.Many2one("xe.classroom", string="Class Room")
    no_of_students = fields.Integer(compute="_compute_no_of_student")
    # old field
    subject = fields.Many2one("xe.subject")
    # new field
    subject_id = fields.Many2one("xe.subject")
    lesson = fields.Char()
    theme = fields.Char()
    topic = fields.Char()
    sub_topic = fields.Char()
    lesson_date = fields.Datetime()
    lesson_plan_ids = fields.One2many("cbc.lesson.plan.line", "lesson_plan_id")
    lesson_plan_header_ids = fields.One2many(
        "cbc.lesson.plan.header.line", "lesson_plan_id"
    )
    scheme_of_work_id = fields.Many2one("cbc.scheme.of.work.line")
    is_lesson_plan = fields.Boolean()
    is_submit = fields.Boolean()
    is_resubmit = fields.Boolean()

    is_manager = fields.Boolean(compute="_is_manager",default=False)
    reflection = fields.Html()

    @api.depends("classroom_id")
    def _compute_no_of_student(self):
        for rec in self:
            rec.no_of_students = 0
            if rec.classroom_id:
                students = self.env["xe.student"].search_count([("classroom_id", "=", rec.classroom_id.id)])
                if students:
                    rec.no_of_students = students

    def _is_manager(self):
        for rec in self:
            if self.env.user.has_group("xe_lesson_planner.group_lesson_plan_manager") and rec.status in ("approved", "rejected"):
                rec.is_manager = True
            elif rec.status in ("departmental_approved", "head_teacher_approved"):
                rec.is_manager = True
            else:
                rec.is_manager = False

    def reset_draft(self):
        self.status = "draft"

    def button_rejected(self):
        self.status = "rejected"

    @api.model
    def create(self, vals):
        if vals:
            vals["seq_name_lp"] = (
                self.env["ir.sequence"].next_by_code("cbc.lesson.plan") or "/"
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
        result = super(CBCLessonPlan, self).create(vals)
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
        result = super(CBCLessonPlan, self).write(vals)
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

            self.env["hr.employee.approval.cbc"].sudo().create(
                {
                    "first_approval": True,
                    "cbc_lesson_plan_id": self.id,
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
        self.status = "approved"

class CBCLessonPlanLine(models.Model):
    _name = "cbc.lesson.plan.line"
    _description = "CBC Lesson Plan Line"
    # _rec_name = "content"

    time = fields.Char()
    learning_experiences = fields.Text()
    content = fields.Text()
    learning_activities = fields.Text()
    learning_resources = fields.Text()
    lesson_plan_id = fields.Many2one("cbc.lesson.plan")

    @api.depends("lesson_plan_id")
    def _compute_roll(self):
        if self.lesson_plan_id:
            if self.lesson_plan_id.classroom_id:
                self.roll = self.lesson_plan_id.classroom_id.capacity
            else:
                self.roll = 0


class CBCLPHeader(models.Model):
    _name = "cbc.lp.header"
    _description = "CBC Lesson Plan header"
    _rec_name = "name"

    name = fields.Char()


class CBCLessonPlanHeaderLine(models.Model):
    _name = "cbc.lesson.plan.header.line"
    _description = "CBC Lesson Plan header Line"
    _rec_name = "cbc_header_id"

    # old field
    cbc_header = fields.Many2one("cbc.lp.header", string="Header")
    # new field
    cbc_header_id = fields.Many2one("cbc.lp.header", string="Header")
    content = fields.Text()
    lesson_plan_id = fields.Many2one("cbc.lesson.plan")

class SpecificLearningOutcomes(models.Model):
    _name = "specific.learning.outcomes"
    _description = "Specific Learning Outcomes"

    name = fields.Char()
    lesson_plan_id = fields.Many2one("cbc.lesson.plan")

class KeyInquiryQuestions(models.Model):
    _name = "key.inquiry.questions"
    _description = "Specific Learning Outcomes"

    name = fields.Char()
    lesson_plan_id = fields.Many2one("cbc.lesson.plan")

class LearningResources(models.Model):
    _name = "learning.resources"
    _description = "Specific Learning Outcomes"

    name = fields.Char()
    lesson_plan_id = fields.Many2one("cbc.lesson.plan")
