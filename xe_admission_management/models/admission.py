import uuid
from datetime import date

from odoo.exceptions import UserError

from odoo import fields, models, api, _


class AdmissionEnquiryForm(models.Model):
    _name = "xe.admission.enquiry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Admission Form"

    def _default_access_token(self):
        return uuid.uuid4().hex

    @api.depends("name")
    def _compute_get_default_type(self):
        for record in self:
            interview_fee_type = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("xe_admission_management.interview_fee_type")
            )
            record.interview_fee_type = interview_fee_type

    def _get_interview_mode(self):
        is_schedule_interview = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_admission_management.is_schedule_interview")
        )
        return is_schedule_interview

    def _compute_get_calender_event_count(self):
        for record in self:
            interview_count = 0
            if record.assigned_id:
                interview_count = self.env["calendar.event"].search_count(
                    [("partner_ids", "in", [record.assigned_id.user_id.partner_id.id])]
                )
            record.calendar_event_count = interview_count

    def _get_academic_year(self):
        academic_rec = self.env.company.current_academic_year_id or False
        return academic_rec

    name = fields.Char(required=True)
    access_token = fields.Char("Invitation Token", default=_default_access_token)
    number = fields.Char(required=True, default="NEW", readonly=True)
    image = fields.Binary()
    previous_school_attended = fields.Char()
    previous_school_mark = fields.Char(string="Previous School Grade(Marks)")
    course_id = fields.Many2one("xe.course", string="Class(To Join)", required=True)
    classroom_id = fields.Many2one("xe.classroom", string="Class Room")
    assigned_id = fields.Many2one("hr.employee", string="Assigned To")
    user_id = fields.Many2one("res.users", string="Assigned To")
    nationality_id = fields.Many2one("res.country")
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")], required=True
    )

    dob = fields.Date(string="Date of Birth")
    academic_year_id = fields.Many2one("xe.academic.year", default=_get_academic_year)
    remarks = fields.Text()
    email = fields.Char()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("assigned", "Assigned"),
            ("interview_scheduled", "Interview Scheduled"),
            ("passed", "Passed"),
            ("failed", "Failed"),
            ("application_created", "Application Created"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    interview_start_date = fields.Datetime(string="Interview Start", tracking=True)
    interview_end_date = fields.Datetime(string="Interview End", tracking=True)
    description = fields.Text(string="Notes")
    pass_reason = fields.Text(string="Remarks(Passed)", tracking=True)
    fail_reason = fields.Text(string="Remarks(Failed)", tracking=True)
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state")
    county = fields.Char()
    zip = fields.Char(string="Postal Code")
    country_id = fields.Many2one("res.country")
    enq_url = fields.Char(string="Enq URL")
    is_sibling = fields.Boolean()

    student_ids = fields.Many2many("xe.student", string="Student Details")
    parent_ids = fields.Many2many("xe.parent", string="Parent Details")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    student_birthcert = fields.Binary("Student Birth Certificate")
    store_fname1 = fields.Char("File Name1")
    previous_term_report = fields.Binary("Student Report Card")
    store_fname9 = fields.Char("File Name9")
    leaving_certificate = fields.Binary("Previous School Leaving Certificate")
    store_fname11 = fields.Char("File Name11")
    father_passport = fields.Binary("National ID Parent 1")
    store_fname3 = fields.Char("File Name3")
    mother_passport = fields.Binary("National ID Parent 2")
    store_fname4 = fields.Char("File Name4")
    passportcopy_father = fields.Binary("Passport Copy of Parent1")
    store_fname5 = fields.Char("File Name5")
    passportcopy_mother = fields.Binary("Passport Copy of Parent2")
    store_fname6 = fields.Char("File Name6")
    is_transport = fields.Boolean()
    is_activity = fields.Boolean()
    is_boarding = fields.Boolean()
    # old field
    fees_to_zone = fields.Many2one("xe.fees.type", string="To Zone", tracking=True)
    # new field
    fees_to_zone_id = fields.Many2one("xe.fees.type", string="To Zone", tracking=True)
    activity_fee_ids = fields.Many2many("xe.fees.type")
    interview_fee_type = fields.Selection(
        [
            ("no", "No Interview Fees"),
            ("general", "General Interview Fees"),
            ("class_wise", "Interview Fees Class Wise"),
        ],
        compute="_compute_get_default_type",
    )
    add_interview_fee = fields.Boolean(
        "Interview fees", related="course_id.is_add_interview_fee"
    )
    interview_fee_inv_id = fields.Many2one(
        "account.move", ondelete="cascade", string="Interview Fees Invoice"
    )
    admn_number = fields.Char()
    is_interview = fields.Boolean(
        "Enable Interview Button", default=_get_interview_mode
    )
    calendar_event_count = fields.Integer(
        "Interview Count", compute="_compute_get_calender_event_count"
    )

    def action_schedule_meeting(self, smart_calendar=True):
        """Open meeting's calendar view to schedule meeting on current opportunity.

        :param smart_calendar: boolean, to set to False if the view should not try to choose relevant
          mode and initial date for calendar view, see ``_get_opportunity_meeting_view_parameters``
        :return dict: dictionary value for created Meeting view"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "calendar.action_calendar_event"
        )
        partner_id = (
            self.assigned_id
            and self.assigned_id.user_id
            and self.assigned_id.user_id.partner_id
            and self.assigned_id.user_id.partner_id.id
            or False
        )
        partner_ids = [partner_id]
        if partner_id:
            partner_ids.append(partner_id)
        if self.student_ids:
            partner_ids.append(self.student_ids.mapped("partner_id").ids)
        action["context"] = {
            "default_partner_id": partner_id,
            "default_partner_ids": partner_ids,
            "default_name": self.name,
        }
        return action

    def action_confirm(self):
        seq_search = self.course_id.classroom_seq_id.code
        seq = self.env["ir.sequence"].next_by_code(seq_search)
        self.admn_number = seq
        enq_seq = self.env["ir.sequence"].next_by_code("xe.admission.inquiry")
        year = str(date.today().year)
        enq_seq = "ENQ/" + year + "/" + enq_seq
        update_vals = {"state": "confirmed", "number": enq_seq}
        if self.add_interview_fee:
            product_id = self.course_id.interview_pdt_id
            if not product_id:
                raise UserError(
                    _("Please define Interview Fee Product for " + self.course_id.name)
                )
            if product_id:
                inv_line_vals = {
                    "product_id": product_id.id,
                    "quantity": 1,
                    "price_unit": product_id.list_price,
                }
                partner = self.env["res.partner"].search(
                    [("is_interview_fee", "=", True)], limit=1
                )
                inv_vals = {
                    "partner_id": partner.id,
                    "invoice_line_ids": [(0, 0, inv_line_vals)],
                    "move_type": "out_invoice",
                }
                move_id = self.env["account.move"].create(inv_vals)
                if move_id:
                    update_vals["interview_fee_inv_id"] = move_id.id
        self.write(update_vals)

    def action_cancel(self):
        self.state = "cancelled"

    def action_assign(self):
        assigned_id = self.assigned_id and self.assigned_id.id
        if not assigned_id:
            raise UserError(_("Please Fill Assign To field first"))
        self.state = "assigned"

    def action_reset_draft(self):
        self.state = "draft"

    def action_open_application(self):
        form_view = self.env.ref("xe_admission_management.view_application_form")
        tree_view = self.env.ref("xe_admission_management.view_application_tree")
        application_id = (
            self.env["xe.application"].search([("enquiry_id", "=", self.id)]).id
        )

        value = {
            "domain": str([("enquiry_id", "=", self.id)]),
            "view_type": "form",
            "view_mode": "tree, form",
            "res_model": "xe.application",
            "view_id": False,
            "views": [
                (form_view and form_view.id or False, "form"),
                (tree_view and tree_view.id or False, "tree"),
            ],
            "type": "ir.actions.act_window",
            "res_id": application_id,
            "target": "current",
        }
        return value

    def action_open_student(self):
        form_view = self.env.ref("xenesis_school_base.view_student_form")
        tree_view = self.env.ref("xenesis_school_base.view_student_tree")
        stud_rec = self.env["xe.student"].search([("name", "=", self.name)], limit=1).id

        value = {
            "domain": str([("id", "=", stud_rec)]),
            "view_type": "form",
            "view_mode": "tree, form",
            "res_model": "xe.student",
            "view_id": False,
            "views": [
                (tree_view and tree_view.id or False, "tree"),
                (form_view and form_view.id or False, "form"),
            ],
            "type": "ir.actions.act_window",
            "res_id": stud_rec,
            "target": "current",
        }
        return value

    @api.onchange("student_ids")
    def onchange_students(self):
        parents = []
        if self.student_ids:
            for i in self.student_ids:
                student_id = self and self.id
                student = student_id if student_id else i._origin.id
                student_parent_rel = (
                    self.env["xe.student"].sudo().search([("id", "=", student)])
                )
                for rec in student_parent_rel.parent_ids:
                    parents.append(rec.id)
            self.parent_ids = [(6, 0, parents)]
        else:
            self.parent_ids = [(6, 0, [])]

    def action_create_application(self):
        self.state = "application_created"
        fee_struct_id = (
            self.env["xe.fees.structure"]
            .sudo()
            .search(
                [
                    ("course_id", "=", self.course_id.id),
                    ("fee_structu_type", "=", "academic"),
                    ("academic_year_id", "=", self.academic_year_id.id),
                ]
            )
        )
        vals = {
            "fee_structure_id": fee_struct_id[0].id if fee_struct_id else None,
            "image": self.image,
            "name": self.number,
            "enquiry_id": self.id,
            "admission_number": self.admn_number,
            "student_name": self.name,
            "previous_school_attended": self.previous_school_attended,
            "previous_school_mark": self.previous_school_mark,
            "course_id": self.course_id.id,
            "classroom_id": self.classroom_id and self.classroom_id.id,
            "assigned_id": self.assigned_id.id,
            "nationality_id": self.nationality_id and self.nationality_id.id,
            "gender": self.gender,
            "dob": self.dob,
            "academic_year_id": self.academic_year_id
            and self.academic_year_id.id
            or False,
            "remarks": self.remarks,
            "email": self.email,
            "street": self.street,
            "street2": self.street2,
            "city": self.city,
            "county": self.county,
            "zip": self.zip,
            "country_id": self.country_id and self.country_id.id,
            "is_transport": self.is_transport,
            "is_activity": self.is_activity,
            "is_boarding": self.is_boarding,
            "fees_to_zone_id": self.fees_to_zone_id.id,
            "activity_fee_ids": self.activity_fee_ids.ids,
            "previous_term_report": self.previous_term_report,
            "store_fname9": self.store_fname9,
            "leaving_certificate": self.leaving_certificate,
            "store_fname11": self.store_fname11,
            "father_passport": self.father_passport,
            "store_fname3": self.store_fname3,
            "mother_passport": self.mother_passport,
            "store_fname4": self.store_fname4,
            "passportcopy_father": self.passportcopy_father,
            "store_fname5": self.store_fname5,
            "passportcopy_mother": self.passportcopy_mother,
            "store_fname6": self.store_fname6,
            "student_birthcert": self.student_birthcert,
            "store_fname1": self.store_fname1,
        }
        self.env["xe.application"].create(vals)
