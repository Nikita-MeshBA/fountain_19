import logging

from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class StudentProfile(models.Model):
    _name = "xe.student"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread"]
    _description = "Student Profile"

    def default_academic_year(self):
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
        else:
            academic_rec = self.company_id.current_academic_year_id
        return academic_rec and academic_rec.id or False

    @api.model
    def default_get(self, fields):
        defaults = super(StudentProfile, self).default_get(fields)
        if "current_academic_year_id" in fields and not defaults.get(
            "current_academic_year_id"
        ):
            config_param = (
                self.env["ir.config_parameter"]
                .sudo()
                .search(
                    [("key", "=", "xenesis_school_base.current_academic_year_id")],
                    limit=1,
                )
            )
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            defaults["current_academic_year_id"] = (
                academic_rec and academic_rec.id or False
            )
        return defaults

    def _compute_company_currency(self):
        for student in self:
            if student.partner_id.company_id:
                student.currency_id = student.partner_id.sudo().company_id.currency_id
            else:
                student.currency_id = self.env.company.currency_id

    roll_number = fields.Char(string="Admission Number")
    dob = fields.Date(string="Date of Birth")
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
    )
    blood_group = fields.Selection(
        [
            ("A+", "A+ve"),
            ("B+", "B+ve"),
            ("O+", "O+ve"),
            ("AB+", "AB+ve"),
            ("A-", "A-ve"),
            ("B-", "B-ve"),
            ("O-", "O-ve"),
            ("AB-", "AB-ve"),
        ],
    )
    nationality_id = fields.Many2one("res.country", "Nationality")
    visa_info = fields.Char()
    partner_id = fields.Many2one(
        "res.partner",
        ondelete="cascade",
        required=True,
        auto_join=True,
        index=True,
    )
    user_id = fields.Many2one("res.users")
    course_detail_ids = fields.One2many("xe.student.course", "student_id")
    company_id = fields.Many2one(
        "res.company",
        index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_company_currency",
        readonly=True,
        help="Utility field to express amount currency",
    )

    course_id = fields.Many2one("xe.course", string="Class")
    classroom_id = fields.Many2one("xe.classroom")
    # stream_id = fields.Many2one("xe.stream")

    term_id = fields.Many2one("xe.term")
    elective_subject_id = fields.Many2one("xe.subject", "Subject")
    parent_user_ids = fields.Many2many("res.users", string="Parent Users")
    remarks = fields.Char()
    nemis = fields.Char()
    assessment_number = fields.Char()

    total_balance_partner = fields.Monetary(
        string="Balance", compute="_compute_partner_balance"
    )
    is_auto_seq = fields.Boolean("Is auto Sequence")
    elective_subjects_ids = fields.Many2many(
        "xe.subject",
        "elective_subjects_rel",
        "subject_id",
        "elective_id",
    )
    mandatory_subjects_ids = fields.Many2many(
        "xe.subject",
        "mandatory_subjects_rel",
        "subject_id",
        "mandatory_id",
    )

    is_siblings = fields.Boolean(default=True)
    student_ids = fields.Many2many(
        "xe.student", "xe_student_siblings_rel", "sid", "eid", string="Student Details"
    )
    parent_ids = fields.Many2many("xe.parent", string="Parent Details")
    list_ids = fields.Char()
    # old field
    academic_year = fields.Many2one("xe.academic.year", string="Joined Academic Year")
    # new field
    academic_year_id = fields.Many2one(
        "xe.academic.year", string="Joined Academic Year"
    )
    # old field
    current_academic_year = fields.Many2one(
        "xe.academic.year", default=default_academic_year
    )
    # new field
    current_academic_year_id = fields.Many2one(
        "xe.academic.year", default=default_academic_year
    )
    joined_date = fields.Date()
    leaving_date = fields.Date(tracking=True)

    hide_acc_balance = fields.Boolean(compute="_compute_hide_account_balance")
    hide_parent_field = fields.Boolean(compute="_compute_hide_parent_field")
    total_invoiced = fields.Monetary(compute="_compute_invoice_total")

    previous_term_report = fields.Binary("Previous Term Report Form")
    student_birthcert = fields.Binary("Student Birth Certificate")
    store_fname1 = fields.Char("File Name1")
    store_fname9 = fields.Char("File Name9")
    leaving_certificate = fields.Binary("Previous School Leaving Certificate")
    store_fname11 = fields.Char("File Name11")
    father_passport = fields.Binary("National ID Parent 1")
    store_fname3 = fields.Char("File Name3")
    mother_passport = fields.Binary("National ID Parent 2")
    store_fname4 = fields.Char("File Name4")
    passportcopy_father = fields.Binary("Passport Copy Parent 1")
    store_fname5 = fields.Char("File Name5")
    passportcopy_mother = fields.Binary("Passport Copy Parent 2")
    store_fname6 = fields.Char("File Name6")
    certificate_number = fields.Char()
    alumni_boolean = fields.Boolean("Alumni Student")
    passing_year_id = fields.Many2one("xe.academic.year", "Passing Academic Year")
    current_position = fields.Char(size=256)
    current_job = fields.Char(size=256)

    @api.onchange("course_detail_ids")
    def _onhange_course_details(self):
        if self.course_detail_ids:
            for i in self.course_detail_ids:
                self.classroom_id = i.classroom_id.id
                self.course_id = i.course_id.id

    def update_current_academic_year_id(self):
        """Update existing student current academic year"""
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            student_rec = self.env["xe.student"].search([])
            for i in student_rec:
                i.current_academic_year_id = academic_rec and academic_rec.id or False

    def _compute_invoice_total(self):
        self.total_invoiced = 0
        for student in self:
            partner_id = student.partner_id and student.partner_id.id
            invoice_ids = self.env["account.move"].search(
                [("partner_id", "=", partner_id), ("move_type", "=", "out_invoice")]
            )
            student.total_invoiced = sum(inv.amount_total for inv in invoice_ids)

    def action_view_invoice(self):
        self.ensure_one()
        student_obj = self
        partner_id = student_obj.partner_id and student_obj.partner_id.id
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        action["domain"] = [
            ("partner_id", "=", partner_id),
            ("move_type", "=", "out_invoice"),
        ]
        action["context"] = {"default_partner_id": partner_id}
        return action

    def _compute_hide_parent_field(self):
        for i in self:
            vals = False
            if i.env.user.has_group("xenesis_school_base.group_xe_admin"):
                vals = False
            elif i.env.user.has_group("xenesis_school_base.group_xe_staff"):
                vals = False
            elif i.env.user.has_group("xenesis_school_base.group_xe_parent"):
                vals = True
            elif i.env.user.has_group("xenesis_school_base.group_xe_student"):
                vals = False
            else:
                vals = False
            i.hide_parent_field = vals

    def _compute_hide_account_balance(self):
        for i in self:
            vals = False
            if i.env.user.has_group("xenesis_school_base.group_xe_admin"):
                vals = False
            elif i.env.user.has_group("xenesis_school_base.group_xe_staff"):
                vals = False
            elif i.env.user.has_group(
                "xenesis_school_base.group_xe_parent"
            ) and i.env.user.has_group(
                "xenesis_school_base.group_student_balance_readonly"
            ):
                vals = True
            elif i.env.user.has_group("xenesis_school_base.group_xe_student"):
                vals = False
            else:
                vals = False

            if i.env.user.has_group(
                "xenesis_school_base.group_student_balance_readonly"
            ):
                vals = True
            i.hide_acc_balance = vals

    def get_grouped(self, val):
        from collections import defaultdict

        res = defaultdict(list)
        for v, k in val:
            res[k].append(v)
        result = [{"date": k, "line_ids": v} for k, v in res.items()]
        return result

    @api.onchange("elective_subjects_ids", "course_id")
    def _onchange_elective_subjects_ids(self):
        if self.course_id:
            mandatory_sub_ids = (
                self.env["xe.subject"]
                .sudo()
                .search(
                    [
                        ("course_ids", "=", self.course_id.id),
                        ("subject_mode", "=", "no"),
                    ]
                )
            )
            self.write({"mandatory_subjects_ids": [(6, 0, mandatory_sub_ids.ids)]})
        else:
            self.mandatory_subjects_ids = False

    @api.onchange("name")
    def _set_auto_seq(self):
        for line in self:
            class_admission_no_automatic = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("xenesis_school_base.class_admission_no_automatic")
                or False
            )
            line.is_auto_seq = class_admission_no_automatic

    # @api.constrains("roll_number")
    # def _check_admision_number(self):
    #     for rec in self:
    #         record = self.env["xe.student"].search(
    #             [("roll_number", "=", rec.roll_number)]
    #         )
    #         if len(record) > 1:
    #             raise ValidationError(_("Admission Number is Duplicate"))

    def add_siblings(self):
        view = self.env.ref("xenesis_school_base.add_siblings_form")
        wiz = self.env["add.siblings.wizard"].create(
            {
                "student_id": self.id,
            }
        )
        # TDE FIXME: a return in a loop, what a good idea. Really.
        return {
            "name": _("Add siblings"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "add.siblings.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wiz.id,
            "context": self.env.context,
        }

    def action_view_siblings(self):
        form_view = self.env.ref("xenesis_school_base.view_student_form_sibling")
        tree_view = self.env.ref("xenesis_school_base.view_student_tree_sibling")
        stud_rec = self.env["xe.student"].search([("id", "in", self.student_ids.ids)])

        value = {
            "domain": str([("id", "in", stud_rec.ids)]),
            "view_type": "form",
            "view_mode": "tree, form",
            "res_model": "xe.student",
            "view_id": False,
            "views": [
                (tree_view and tree_view.id or False, "tree"),
                (form_view and form_view.id or False, "form"),
            ],
            "type": "ir.actions.act_window",
            "res_ids": stud_rec.ids,
            "target": "current",
        }
        return value

    @api.model
    def create(self, vals):
        class_admission_no_automatic = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xenesis_school_base.class_admission_no_automatic")
            or False
        )
        if class_admission_no_automatic:
            course_id = vals.get("course_id")

            if not course_id:
                raise UserError(_("Kindly define Class"))
            classroom_obj = self.env["xe.course"].browse(course_id)
            classroom_seq_id = classroom_obj.classroom_seq_id

            if not classroom_seq_id:
                raise UserError(
                    _("Kindly define Sequence inside the class you selected")
                )
            seq_code = (
                classroom_obj.classroom_seq_id
                and classroom_obj.classroom_seq_id.code
                or ""
            )

            if not seq_code:
                raise UserError(
                    _("Kindly define Sequence code inside the class sequence")
                )
            if not vals.get("roll_number"):
                seq = self.env["ir.sequence"].next_by_code(seq_code)
                vals["roll_number"] = seq

        result = super(StudentProfile, self).create(vals)

        # Mandatory Subjects
        if result.course_id:
            mandatory_sub_ids = (
                self.env["xe.subject"]
                .sudo()
                .search(
                    [
                        ("course_ids", "=", result.course_id.id),
                        ("subject_mode", "=", "no"),
                        ("company_id", "=", result.company_id.id),
                    ]
                )
            )
            result.write({"mandatory_subjects_ids": [(6, 0, mandatory_sub_ids.ids)]})
        else:
            result.write({"mandatory_subjects_ids": [(6, 0, [])]})

        partner_id = result.partner_id
        parent_ids = []
        if result.student_ids.parent_ids:
            for parent in result.student_ids.parent_ids:
                parent_ids.append(parent.id)
        if parent_ids:
            parent_ids = [(6, 0, parent_ids)]
            result.parent_ids = parent_ids

        # Sibling ID map
        sibling_rec = result.student_ids + result

        students = []
        for s in result.student_ids:
            students.append(s.id)
        students.append(result.id)

        latest_student = students
        for i in sibling_rec:
            if i.id in latest_student:
                latest_student.remove(i.id)
            i.student_ids = [(6, 0, latest_student)]
            latest_student.append(i.id)

        category_obj = self.env["res.partner.category"].search(
            [("name", "=", "Student")]
        )
        if not (category_obj and category_obj.id):
            raise UserError(_("Did not found Category name Student in Contacts form"))
        partner_id.write(
            {
                "user_type": "student",
                "company_id": result.company_id.id,
                "category_id": [(6, 0, [category_obj.id])],
            }
        )
        # self.clear_caches()
        return result

    def action_view_medcheckup(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "xenesis_school_base.act_medical_checkup"
        )
        action["domain"] = [
            ("partner_id", "=", self.partner_id.id),
        ]
        action["context"] = {
            "default_partner_id": self.partner_id.id,
            "default_type_record": "s",
        }
        return action

    def action_view_parent(self):
        self.ensure_one()
        student_id = self and self.id
        parents = []
        student_parent_rel = self.env["xe.student.parent"].search(
            [("student_id", "=", student_id)]
        )
        for rec in student_parent_rel:
            parents.append(rec.parent_id and rec.parent_id.id)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "xenesis_school_base.act_parent"
        )
        action["domain"] = [
            ("id", "in", parents),
        ]
        student_information = [(5, 0, 0)]
        academic_lines = self.course_detail_ids
        term_values = []
        course_values = []
        for line in academic_lines:
            term_values.append(line.term_id and line.term_id.id or False)
            course_values.append(line.course_id and line.course_id.id or False)

        line = (
            0,
            0,
            {
                "student_id": student_id,
                "roll_number": self.roll_number,
                "course_ids": [(6, 0, course_values)],
                "term_ids": [(6, 0, term_values)],
            },
        )
        student_information.append(line)
        action["context"] = {"default_student_detail_ids": student_information}
        return action

    @api.onchange("course_id", "classroom_id")
    def _onchange_course_id(self):
        student_parent_rec = (
            self.env["xe.student.parent"]
            .sudo()
            .search([("student_id", "=", self._origin.id)])
        )
        if student_parent_rec:
            for p in student_parent_rec:
                # Class Updated
                courses = []
                if self.course_id:
                    courses.append(self.course_id and self.course_id.id)
                if courses:
                    p.course_ids = [(6, 0, courses)]
                else:
                    p.course_ids = [(6, 0, courses)]

                # Class Room Updated
                classroom = []
                if self.classroom_id:
                    classroom.append(self.classroom_id and self.classroom_id.id)
                if classroom:
                    p.class_room_ids = [(6, 0, classroom)]
                else:
                    p.class_room_ids = [(6, 0, classroom)]

    def action_view_migration_history(self):
        self.ensure_one()
        student_id = self and self.id
        action = self.env["ir.actions.actions"]._for_xml_id(
            "xenesis_school_base.act_migration_history"
        )
        action["domain"] = [
            ("student_id", "=", student_id),
        ]
        return action

    def action_view_activity_logs(self):
        self.ensure_one()
        student_id = self and self.id
        staff_id = (
            self.env["hr.employee"].search([("user_id", "=", self._uid)], limit=1)
            and self.env["hr.employee"]
            .search([("user_id", "=", self._uid)], limit=1)
            .id
            or False
        )

        action = self.env["ir.actions.actions"]._for_xml_id(
            "xenesis_school_base.act_activity"
        )
        action["domain"] = [
            ("student_id", "=", student_id),
        ]
        action["context"] = {
            "default_student_id": student_id,
            "default_teacher_id": staff_id,
        }
        return action

    def get_account_move_lines(self, partner_ids):
        # self.env.cr.execute(
        #     "SELECT m.name AS move_id, l.date, l.name, l.ref, l.date_maturity, \
        #     l.partner_id, l.blocked, l.amount_currency, l.currency_id, "
        #     "CASE WHEN at = 'receivable' "
        #     "THEN SUM(l.debit) "
        #     "ELSE SUM(l.credit * -1) "
        #     "END AS debit, "
        #     "CASE WHEN at.type = 'receivable' "
        #     "THEN SUM(l.credit) "
        #     "ELSE SUM(l.debit * -1) "
        #     "END AS credit, "
        #     "CASE WHEN l.date_maturity < %s "
        #     "THEN SUM(l.debit - l.credit) "
        #     "ELSE 0 "
        #     "END AS mat "
        #     "FROM account_move_line l "
        #     "JOIN account_account aa ON (l.account_id = aa.id) "
        #     "JOIN account_account_type at ON (aa.user_type_id = at.id) "
        #     "JOIN account_move m ON (l.move_id = m.id) "
        #     "WHERE l.partner_id IN %s AND at.type IN ('receivable', 'payable') \
        #     AND m.state='posted' AND l.full_reconcile_id IS NULL GROUP BY l.date, \
        #     l.name, l.ref, l.date_maturity, l.partner_id, at.type, l.blocked, \
        #     l.amount_currency, l.currency_id, l.move_id, m.name",
        #     ((fields.date.today(),) + (tuple(partner_ids),)),
        # )
        # result = self.env.cr.dictfetchall()
        # return result
        self.env.cr.execute(
            "SELECT m.name AS move_id, l.date, l.name, l.ref, l.date_maturity, \
            l.partner_id, l.blocked, l.amount_currency, l.currency_id, "
            "CASE WHEN aa.account_type = 'asset_receivable' "
            "THEN SUM(l.debit) "
            "ELSE SUM(l.credit * -1) "
            "END AS debit, "
            "CASE WHEN aa.account_type = 'asset_receivable' "
            "THEN SUM(l.credit) "
            "ELSE SUM(l.debit * -1) "
            "END AS credit, "
            "CASE WHEN l.date_maturity < %s "
            "THEN SUM(l.debit - l.credit) "
            "ELSE 0 "
            "END AS mat "
            "FROM account_move_line l "
            "JOIN account_account aa ON (l.account_id = aa.id) "
            "JOIN account_move m ON (l.move_id = m.id) "
            "WHERE l.partner_id IN %s AND aa.account_type IN ('asset_receivable', 'liability_payable') \
            AND m.state='posted' AND l.full_reconcile_id IS NULL GROUP BY l.date, \
            l.name, l.ref, l.date_maturity, l.partner_id, aa.account_type, l.blocked, \
            l.amount_currency, l.currency_id, l.move_id, m.name",
            ((fields.date.today(),) + (tuple(partner_ids),)),
        )
        result = self.env.cr.dictfetchall()
        return result

    @api.depends("partner_id", "partner_id.payment_token_ids")
    def _compute_partner_balance(self):
        for rec in self:
            balance = 0
            partner_id = rec.partner_id and rec.partner_id.id or False
            lines = []
            if partner_id:
                lines = rec.get_account_move_lines([partner_id])
            debit = 0
            credit = 0
            for line in lines:
                if line["move_id"]:
                    debit = debit + line["debit"]
                    credit = credit + line["credit"]
            balance = debit - credit
            rec.total_balance_partner = balance

    def action_clearance_form(self):
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "xe.clearance.form.wizard",
            "target": "new",
            "context": {"default_student_id": self.env.context.get("active_id")},
            "name": _("Clearance Form"),
        }
        return action

    def action_leave_certificate_form(self):
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "xe.certificate.wizard",
            "target": "new",
            "context": {"default_student_id": self.env.context.get("active_id")},
            "name": _("Leaving Certificate"),
        }
        student = self.env["xe.student"].browse(self.env.context.get("active_id"))
        if student and student.application_id.course_id:
            action["context"][
                "default_enrolled_course_id"
            ] = student.application_id.course_id.id
        return action

    @api.onchange("alumni_boolean")
    def onchange_alumni_boolean(self):
        alumni_boolean = self.alumni_boolean
        if alumni_boolean:
            self.alumni_boolean = True
            self.active = False

    def set_alumni_student(self):
        students = self.env["xe.student"].browse(self.env.context.get("active_ids"))
        for student in students:
            student.alumni_boolean = True
            student.active = False

    def write(self, vals):
        if vals.get("alumni_boolean") and vals.get("alumni_boolean") is True:
            vals["active"] = False
        if "alumni_boolean" in vals and vals.get("alumni_boolean") is False:
            vals["active"] = True
        return super(StudentProfile, self).write(vals)
