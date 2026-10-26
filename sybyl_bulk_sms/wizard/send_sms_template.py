from odoo.exceptions import UserError

from odoo import api, fields, models, _


class SmsTemplate(models.TransientModel):
    _name = "send.sms.template.new"
    _description = "Send SMS Template"

    def _default_gateway_account(self):
        account_id = (
            self.env["sms.gateway.config"].search([("active", "=", True)], limit=1).id
        )
        return account_id

    name = fields.Char()
    template_body = fields.Text("Body", translate=True, help="Plain text of message")
    msg_to = fields.Char(string="To Mobile")
    sms_account_gateway_id = fields.Many2one(
        "sms.gateway.config",
        string="Account",
        default=_default_gateway_account,
    )
    filter_by = fields.Selection(
        [
            ("employee", "Employee"),
            ("student", "Student-wise"),
            ("classroom", "Classroom-wise"),
            ("contact", "Contact"),
        ],
        default="employee",
        string="Send By",
    )
    emp_send_by = fields.Selection(
        [("department", "Department-wise"), ("employee", "Employee-wise")],
        default="department",
        string="Based on",
    )
    send_parents = fields.Boolean("Send to Parent Mobile")
    department_ids = fields.Many2many("hr.department", string="Department")
    employee_ids = fields.Many2many("hr.employee", string="Employee")
    student_ids = fields.Many2many("xe.student", string="Student")
    classroom_ids = fields.Many2many("xe.classroom", string="Classroom")
    partner_ids = fields.Many2many("res.partner")

    @api.constrains("template_body")
    def _check_message_length(self):
        if len(self.template_body) > 160:
            raise UserError(_("Message length should not exceed 160 characters"))

    def send_sms_new(self):
        gateway_model = self.sms_account_gateway_id
        if gateway_model:
            emp_mobiles = []
            if self.filter_by == "employee":
                if self.emp_send_by == "department":
                    for dept in self.department_ids:
                        dpt_mobiles = dept.member_ids.mapped("mobile_phone")
                        if dpt_mobiles:
                            emp_mobiles.extend(dpt_mobiles)
                else:
                    if self.employee_ids:
                        emp_mobs = self.employee_ids.mapped("mobile_phone")
                        emp_mobiles.extend(emp_mobs)
            elif self.filter_by == "student":
                parents = self.env["xe.parent"].search(
                    [("student_ids", "in", self.student_ids.ids)]
                )
                parent_mobiles = parents.mapped("mobile")
                if parent_mobiles:
                    emp_mobiles.extend(parent_mobiles)
                if self.student_ids:
                    student_mobile = self.student_ids.mapped("mobile")
                    if student_mobile:
                        emp_mobiles.extend(student_mobile)
            elif self.filter_by == "classroom":
                student_course_ids = self.env["xe.classroom"].search(
                    [("id", "in", self.classroom_ids.ids)]
                )
                student_details = self.env["xe.student"].search(
                    [("classroom_id", "in", student_course_ids.ids)]
                )
                parent_mobiles = student_details.parent_ids.mapped("mobile")
                if parent_mobiles:
                    emp_mobiles.extend(parent_mobiles)
                student_mobile = student_details.mapped("mobile")
                if student_mobile:
                    emp_mobiles.extend(student_mobile)
            elif self.filter_by == "contact":
                for partner in self.partner_ids:
                    if partner.mobile:
                        emp_mobiles.append(partner.mobile)

            if emp_mobiles:
                emp_mobiles = list(filter(bool, emp_mobiles))
                gateway_model.send_sms(emp_mobiles, self.template_body)
        else:
            raise UserError(_("Gateway not defined in SMS Template"))
