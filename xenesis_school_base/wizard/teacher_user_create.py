from odoo.exceptions import ValidationError
from odoo import api, fields, models, SUPERUSER_ID, _


class TeacherUser(models.TransientModel):
    _name = "xe.teacher.user"
    _description = "User Create For Teacher"

    teacher_line_ids = fields.One2many(
        "xe.teacher.user.wizard.line", "wizard_id", "Teachers Details"
    )

    @api.model
    def default_get(self, fields):
        res = super(TeacherUser, self).default_get(fields)
        active_ids = self.env.context.get("active_ids", []) or []
        teachers_lines = [(5, 0, 0)]
        teacher_objects = self.env["hr.employee"].browse(active_ids)
        for teacher in teacher_objects:
            line = (
                0,
                0,
                {
                    "teacher_id": teacher.id,
                    "mobile": teacher.mobile,
                    "email": teacher.email,
                    "nationality_id": teacher.nationality_id
                    and teacher.nationality_id.id
                    or False,
                },
            )
            teachers_lines.append(line)
        res.update({"teacher_line_ids": teachers_lines})
        return res

    def create_user(self):
        teacher_user_group = self.env.ref("xenesis_school_base.group_xe_staff")
        active_ids = self.env.context.get("active_ids", []) or []
        lines = self.teacher_line_ids
        for line in lines:
            if line.teacher_id.employee_id and line.teacher_id.employee_id.id:
                raise ValidationError(
                    _(
                        "Employee ID already existing with the following Teacher: %s.",
                        line.teacher_id.name,
                    )
                )
            partner_id = line.teacher_id.partner_id or False
            employee_id = self.env["hr.employee"].create(
                {
                    "name": line.teacher_id.name,
                    "mobile_phone": line.teacher_id.mobile,
                    "work_email": line.teacher_id.email,
                    "country_id": line.teacher_id.nationality_id
                    and line.teacher_id.nationality_id.id,
                    "gender": line.teacher_id.gender,
                    "birthday": line.teacher_id.dob,
                    "visa_no": line.teacher_id.visa_info,
                    "private_street": partner_id.street
                    if partner_id and partner_id.street
                    else "",
                    "private_street2": partner_id.street2
                    if partner_id and partner_id.street2
                    else "",
                    "private_city": partner_id.city
                    if partner_id and partner_id.city
                    else "",
                    "private_zip": partner_id.zip
                    if partner_id and partner_id.zip
                    else "",
                    "private_state_id": partner_id.state_id.id
                    if partner_id and partner_id.state_id
                    else "",
                    "private_country_id": partner_id.country_id.id
                    if partner_id and partner_id.country_id
                    else "",
                }
            )
            line.teacher_id.employee_id = employee_id
            if line.create_user:
                user_obj = self.env["res.users"].search(
                    [("login", "=", line.teacher_id.email)], limit=1
                )
                if user_obj:
                    raise ValidationError(
                        _(
                            "User already existing with the following Teacher: %s.",
                            line.teacher_id.name,
                        )
                    )

                if not line.teacher_id.user_id:
                    vals = {
                        "name": line.teacher_id.name,
                        "login": line.teacher_id.email,
                        "partner_id": line.teacher_id.partner_id.id,
                    }
                    user_id = self.env["res.users"].create(vals)
                    line.teacher_id.user_id = user_id
                    teacher_user_group.users = teacher_user_group.users + user_id
                    line.teacher_id.employee_id.user_id = user_id


class TeacherUserLineDetails(models.TransientModel):
    _name = "xe.teacher.user.wizard.line"
    _description = "Teacher line Details"

    wizard_id = fields.Many2one("xe.teacher.user", "Wizard", ondelete="cascade")
    teacher_id = fields.Many2one("hr.employee", "Name", required=True)
    nationality_id = fields.Many2one("res.country")
    mobile = fields.Char()
    email = fields.Char()
    create_user = fields.Boolean(string="CreateUser", default=True)

    @api.onchange("teacher_id")
    def _onchange_teacher_id(self):
        if self.teacher_id and self.teacher_id.id:
            mobile = self.teacher_id.mobile
            email = self.teacher_id.email
            nationality_id = (
                self.teacher_id.nationality_id
                and self.teacher_id.nationality_id.id
                or False
            )
            self.write(
                {"mobile": mobile, "email": email, "nationality_id": nationality_id}
            )
