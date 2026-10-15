from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, _


class StaffProfile(models.Model):
    _name = "xe.staff"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread"]
    _description = "Staff Profile"

    dob = fields.Date(string="Date of Birth")
    user_id = fields.Many2one("res.users", "User")
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
    nationality_id = fields.Many2one("res.country")
    visa_info = fields.Char()
    partner_id = fields.Many2one("res.partner", ondelete="cascade", required=True)
    subject_ids = fields.Many2many("xe.subject", string="Subject(s)")
    assigned_course_id = fields.Many2one("xe.course", string="Class")
    assigned_term_id = fields.Many2one("xe.term", string="Term")
    employee_id = fields.Many2one("hr.employee", string="Employee Ids")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

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
            "default_type_record": "t",
        }
        return action

    @api.model
    def create(self, vals):
        result = super(StaffProfile, self).create(vals)
        partner_id = result.partner_id
        category_obj = self.env["res.partner.category"].search(
            [("name", "=", "Teacher")]
        )
        if not (category_obj and category_obj.id):
            raise UserError(_("Did not found Category name Teacher in Contacts form"))
        partner_id.write(
            {"user_type": "teacher", "category_id": [(6, 0, [category_obj.id])]}
        )
        return result


class Employee(models.Model):
    _inherit = "hr.employee"

    teach_type = fields.Selection(
        [("teaching", "Teaching"), ("non", "Non Teaching")],
        default="non",
        string="Type",
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
    ''' subject_ids(many2many) fields replace with subjects_ids(one2many) after migration '''
    subject_ids = fields.Many2many("xe.assignsubject", string="Subject(s)")
    subjects_ids = fields.One2many('xe.assignsubject', 'employee_id', string='Subject(s)')
    ''' <<--->> '''
    assigned_course_id = fields.Many2one("xe.course", string="Class")
    assigned_term_id = fields.Many2one("xe.term", string="Term")
    partner_id = fields.Many2one("res.partner", required=True)

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
            "default_type_record": "t",
        }
        return action

    def create_user(self):
        res_users = (
            self.env["res.users"]
            .sudo()
            .search([("login", "=", self.work_email), ("name", "=", self.name)])
        )
        if not res_users:
            res_users = (
                self.env["res.users"]
                .sudo()
                .create(
                    {
                        "login": self.work_email,
                        "name": self.name,
                    }
                )
            )
        self.user_id = res_users.id

    @api.model
    def create(self, vals):
        # self.clear_caches()
        return super(Employee, self).create(vals)

    def write(self, vals):
        # self.clear_caches()
        return super(Employee, self).write(vals)


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    teach_type = fields.Selection(
        [("teaching", "Teaching"), ("non", "Non Teaching")],
        default="non",
        string="Type",
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
    assigned_course_id = fields.Many2one("xe.course", string="Class")
    assigned_term_id = fields.Many2one("xe.term", string="Term")
    partner_id = fields.Many2one("res.partner", required=True)


class HrEmployeeCreateUserWizard(models.TransientModel):
    _name = "hr.employee.create.user.wizard"
    _description = "Hr Employee Create User Wizard"

    def create_user_action(self):
        emp_rec = self.env["hr.employee"].search(
            [("id", "in", self._context["active_ids"])]
        )
        for i in emp_rec:
            if i.work_email:
                res_users = (
                    self.env["res.users"]
                    .sudo()
                    .search([("login", "=", i.work_email), ("name", "=", i.name)])
                )
                if not res_users:
                    res_users = (
                        self.env["res.users"]
                        .sudo()
                        .create(
                            {
                                "login": i.work_email,
                                "name": i.name,
                                "email": i.work_email,
                            }
                        )
                    )
                i.user_id = res_users.id
            else:
                raise ValidationError(
                    _(
                        "Work Email is not configured for Employee Name: %s and Employee ID: %s. "
                        "Please configure Work Email !" % (i.name, i.id)
                    )
                )
