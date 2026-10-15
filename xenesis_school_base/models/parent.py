from odoo.exceptions import UserError

from odoo import api, fields, models, _


class ParentProfile(models.Model):
    _name = "xe.parent"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread"]
    _rec_name = "name"
    _description = "Parent Profile"

    dob = fields.Date(string="Date of Birth")
    user_id = fields.Many2one(
        "res.users",
        "User",
    )
    student_user_ids = fields.Many2many("res.users", string="Student Users")
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
    education = fields.Char()
    yearly_income = fields.Char()
    relation = fields.Selection(
        [("father", "Father"), ("mother", "Mother"), ("guardian", "Guardian")],
    )
    student_detail_ids = fields.One2many(
        "xe.student.parent", "parent_id", "Student Details"
    )
    partner_id = fields.Many2one(
        "res.partner", "Partner", ondelete="cascade", required=True
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    student_ids = fields.Many2many("xe.student", string="Student(s)")

    @api.model
    def create(self, vals):
        result = super(ParentProfile, self).create(vals)
        partner_id = result.partner_id
        category_obj = self.env["res.partner.category"].search(
            [("name", "=", "Parent")]
        )
        if not (category_obj and category_obj.id):
            raise UserError(_("Did not found Category name Parent in Contacts form"))

        partner_id.write(
            {
                "user_type": "parent",
                "company_id": result.company_id.id,
                "category_id": [(6, 0, [category_obj.id])],
            }
        )
        return result

    def write(self, vals):
        result = super(ParentProfile, self).write(vals)
        student_deatil_line = self.student_detail_ids
        for line in student_deatil_line:
            user_ids = []
            already_linked_parents = line.student_id.parent_user_ids
            for p in already_linked_parents:
                user_ids.append(p and p.id)
            if self.user_id:
                user_ids.append(self.user_id and self.user_id.id)
                line.student_id.write({"parent_user_ids": [(6, 0, user_ids)]})

        # Parent data update to student profile
        parents = []
        for line in student_deatil_line:
            student = line.student_id
            student_parent_rel = self.env["xe.student.parent"].search(
                [("student_id", "=", student.id), ("parent_id", "=", self.id)]
            )
            if student_parent_rel:
                for rec in student_parent_rel:
                    parents.append(rec.parent_id and rec.parent_id.id)
                parent_ids = [(6, 0, parents)]
            else:
                parent_ids = [(6, 0, [])]
            line.student_id.write({"parent_ids": parent_ids})
        return result

    # Delete Function
    def fun_delete(self):
        parent_id = self.id
        xe_stud_parent_rec = (
            self.env["xe.student.parent"].sudo().search([("parent_id", "=", parent_id)])
        )
        student_id = xe_stud_parent_rec.student_id
        for i in xe_stud_parent_rec:
            i.unlink()

        if student_id:
            for i in student_id.parent_ids:
                if i.id == parent_id:
                    student_id.write({"parent_ids": [(3, parent_id)]})

    def action_create_user(self):
        self.ensure_one()
        if self.user_id:
            raise UserError(_("User already exists."))
        if not self.email:
            raise UserError(_("Parent email is required."))

        generic_password = self.env[
            'ir.config_parameter'
        ].sudo().get_param(
            'xenesis_school_base.parent_generic_password'
        )
        if not generic_password:
            raise UserError(
                _("Please configure parent generic password in settings.")
            )

        internal_group = self.env.ref('base.group_user')
        parent_group = self.env.ref('xenesis_school_base.group_xe_parent')
        student_group = self.env.ref('xenesis_school_base.group_xe_student')
        balance_group = self.env.ref('xenesis_school_base.group_student_balance_readonly')
        hide_action_group = self.env.ref('xenesis_school_base.group_hide_action')

        group_ids = {internal_group.id, parent_group.id, student_group.id, balance_group.id, hide_action_group.id}

        user_vals = {
            'name': self.name,
            'login': self.email,
            'partner_id': self.partner_id.id,
            'groups_id': [(6, 0, list(group_ids))],
        }
        user = self.env['res.users'].sudo().with_context(
            no_reset_password=True
        ).create(user_vals)
        user.sudo().write({
            'password': generic_password
        })
        self.user_id = user.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'xe.parent',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

class StudentParentDetails(models.Model):
    _name = "xe.student.parent"
    _description = "Student Details"

    parent_id = fields.Many2one("xe.parent", "Parent", ondelete="cascade")
    student_id = fields.Many2one("xe.student", "Name")
    course_ids = fields.Many2many("xe.course", string="Class")
    class_room_ids = fields.Many2many("xe.classroom", string="Class Room")
    term_ids = fields.Many2many("xe.term", string="Term")
    roll_number = fields.Char(
        string="Admission Number", related="student_id.roll_number"
    )

    # student profile parent data remove same time removed parent profile student data
    def fun_delete(self):
        student_id = self.student_id.id
        parent_id = self.parent_id.id
        xe_stud_parent_rec = (
            self.env["xe.student.parent"]
            .sudo()
            .search(
                [("student_id", "=", student_id), ("parent_id", "=", self.parent_id.id)]
            )
        )
        for i in xe_stud_parent_rec:
            i.unlink()

        student_rec = self.env["xe.student"].sudo().search([("id", "=", student_id)])
        if student_rec:
            for i in student_rec.parent_ids:
                if i.id == parent_id:
                    student_rec.write({"parent_ids": [(3, parent_id)]})

    def _add_term_course(self, stud_obj, vals):
        term_values = []
        course_values = []
        academic_lines = stud_obj.course_detail_ids
        for line in academic_lines:
            if line.term_id:
                term_values.append(line.term_id and line.term_id.id or False)
            if line.course_id:
                course_values.append(line.course_id and line.course_id.id or False)
        if course_values:
            vals["course_ids"] = [(6, 0, course_values)]
        if term_values:
            vals["term_ids"] = [(6, 0, term_values)]
        return vals

    @api.model
    def create(self, vals):
        if vals.get("student_id"):
            stud_obj = self.env["xe.student"].browse(vals.get("student_id"))
            vals = self._add_term_course(stud_obj, vals)
        result = super(StudentParentDetails, self).create(vals)
        return result

    def write(self, vals):
        if "student_id" in vals:
            stud_obj = self.env["xe.student"].browse(vals.get("student_id"))
            vals = self._add_term_course(stud_obj, vals)
        result = super(StudentParentDetails, self).write(vals)
        return result

    @api.onchange("student_id")
    def _onchange_student_id(self):
        if self.student_id and self.student_id.id:
            term_values = []
            course_values = []
            academic_lines = self.student_id.course_detail_ids
            for line in academic_lines:
                if line.term_id:
                    term_values.append(line.term_id and line.term_id.id)
                if line.course_id:
                    course_values.append(line.course_id and line.course_id.id)
            if course_values:
                self.course_ids = [(6, 0, course_values)]
            if term_values:
                self.term_ids = [(6, 0, term_values)]


