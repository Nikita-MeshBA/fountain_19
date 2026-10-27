""" Hostel Admission python file """
# pylint: disable= E0401, R0903, R0801, C0116
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HostelAdmission(models.Model):
    """Hostel Admission class"""

    _name = "xe.hostel.admission"
    _description = "Hostel Admission"

    name = fields.Char()
    member_type = fields.Selection(
        [("is_student", "Student"), ("is_faculty", "Faculty")], default="is_student"
    )
    student_id = fields.Many2one("xe.student")
    student_name = fields.Char(related="student_id.name")
    employee_id = fields.Many2one("hr.employee")
    dob = fields.Date(string="Date of Birth")
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
    )
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state", domain="[('country_id', '=?', country_id)]"
    )
    country_id = fields.Many2one("res.country")
    hostel_id = fields.Many2one(
        "xe.hostel", compute="_compute_hostel_details", store=True
    )
    room_id = fields.Many2one("xe.hostel.room", compute="_compute_hostel_details")
    bed_id = fields.Many2one("xe.hostel.bed", compute="_compute_hostel_details", store=True)
    vacated_date = fields.Date(compute="_compute_hostel_details")
    room_member_ids = fields.One2many("xe.hostel.room.member", "hostel_admission_id")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("allocated", "Allocated"),
            ("vacated", "Vacated"),
        ],
        default="draft",
    )
    number = fields.Char(compute="_compute_number_image")
    image = fields.Binary(compute="_compute_number_image")

    @api.depends('student_id', 'employee_id')
    def _compute_number_image(self):
        for rec in self:
            rec.number = ''
            rec.image = False
            if rec.student_id:
                rec.number = rec.student_id.roll_number or ''
                rec.image = rec.student_id.image_1920 or False
            if rec.employee_id:
                rec.number = rec.employee_id.identification_id or ''
                rec.image = rec.employee_id.image_1920 or False

    @api.onchange("student_id")
    def _onchnage_student_id(self):
        if self.student_id:
            self.employee_id = False
            self.image = self.student_id.image_1920 or False
            self.number = self.student_id.roll_number or False
            self.dob = self.student_id.dob or False
            self.gender = self.student_id.gender or False
            self.email = self.student_id.email or ""
            self.phone = self.student_id.phone or ""
            self.mobile = self.student_id.mobile or ""
            self.street = self.student_id.street or ""
            self.street2 = self.student_id.street2 or ""
            self.zip = self.student_id.zip or ""
            self.city = self.student_id.city or ""
            self.state_id = (
                self.student_id.state_id and self.student_id.state_id.id or False
            )
            self.country_id = (
                self.student_id.country_id and self.student_id.country_id.id or False
            )

    @api.onchange("employee_id")
    def _onchnage_employee_id(self):
        if self.employee_id:
            self.student_id = False
            self.image = self.employee_id.image_1920 or False
            self.number = self.employee_id.employee_no or False
            self.dob = self.employee_id.birthday or False
            self.gender = self.employee_id.gender or False
            self.email = self.employee_id.work_email or ""
            self.phone = self.employee_id.work_phone or ""
            self.mobile = self.employee_id.mobile_phone or ""
            self.street = self.employee_id.private_street or ""
            self.street2 = self.employee_id.private_street2 or ""
            self.zip = self.employee_id.private_zip or ""
            self.city = self.employee_id.private_city or ""
            self.state_id = (
                self.employee_id.private_state_id
                and self.employee_id.private_state_id.id
                or False
            )
            self.country_id = (
                self.employee_id.private_country_id
                and self.employee_id.private_country_id.id
                or False
            )

    @api.depends("room_member_ids")
    def _compute_hostel_details(self):
        for rec in self:
            if rec.room_member_ids:
                rec.hostel_id = rec.room_member_ids[-1].hostel_id.id
                rec.room_id = rec.room_member_ids[-1].room_id.id
                rec.bed_id = rec.room_member_ids[-1].bed_id.id
                rec.vacated_date = rec.room_member_ids[-1].vacated_date
            else:
                rec.hostel_id = False
                rec.room_id = False
                rec.bed_id = False
                rec.vacated_date = False

    def button_allocate(self):
        if self.bed_id and self.student_id:
            self.bed_id.student_id = self.student_id.id
        self.state = "allocated"

    def button_vacate(self):
        if self.bed_id:
            self.bed_id.student_id = False
        self.state = "vacated"

    def button_reallocate(self):
        self.state = "draft"

    @api.model
    def create(self, values):
        if values.get("student_id", False):
            admission_id = self.search([("student_id", "=", values.get("student_id"))])
            if admission_id:
                raise ValidationError(
                    _(
                        "Admission number - %s aleady applied for admission."
                        % (admission_id.student_id.roll_number)
                    )
                )

        if values.get("employee_id", False):
            admission_id = self.search(
                [("employee_id", "=", values.get("employee_id"))]
            )
            if admission_id:
                raise ValidationError(
                    _(
                        "Name - %s aleady applied for admission."
                        % (admission_id.employee_id.name)
                    )
                )
        res = super(HostelAdmission, self).create(values)

        if res.member_type == "is_student":
            res.name = res.student_id and res.student_id.name or ""
        if res.member_type == "is_faculty":
            res.name = res.employee_id and res.employee_id.name or ""
        return res

    def write(self, vals):
        res = super(HostelAdmission, self).write(vals)
        if vals.get("student_id"):
            self.name = self.student_id and self.student_id.name or ""
        if vals.get("employee_id"):
            self.name = self.employee_id and self.employee_id.name or ""
        return res
