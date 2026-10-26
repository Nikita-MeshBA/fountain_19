from datetime import datetime

from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, _


class ApplicationForm(models.Model):
    _name = "xe.application"
    _inherit = ["mail.thread"]
    _description = "Application Form"

    # @api.onchange("course_id")
    # def onchange_course(self):
    #     self.term_id = False
    #     term_id = False
    #     if self.course_id and self.course_id.fees_term_id:
    #         term_id = self.course_id.fees_term_id.id
    #     # self.fees_term_id = term_id
    fee_structure_id = fields.Many2one(
        "xe.fees.structure", string="Fees Structure", ondelete="cascade"
    )
    name = fields.Char(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("enrolled", "Enrolled"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    enquiry_id = fields.Many2one("xe.admission.enquiry", "Enquiry")
    student_name = fields.Char(required=True)
    previous_school_attended = fields.Char()
    previous_school_mark = fields.Char(string="Previous School Grade(Marks)")
    course_id = fields.Many2one("xe.course", string="Class(To Join)", required=True)
    classroom_id = fields.Many2one("xe.classroom", string="Class Room")
    term_id = fields.Many2one("xe.term", string="Term")
    stream_id = fields.Many2one("xe.stream", string="House")
    assigned_id = fields.Many2one("hr.employee", string="Assigned To")
    nationality_id = fields.Many2one("res.country", string="Nationality")
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")], required=True
    )
    is_transport = fields.Boolean(string="Include Transport Fee")
    is_activity = fields.Boolean(string="Include Activity Fee")
    is_boarding = fields.Boolean(string="Include Boarding Fee")
    is_optional = fields.Boolean(string="Include Optional Fee")

    @api.onchange("is_transport", "is_activity", "is_optional")
    def _onchange_tac(self):
        if self.is_transport or self.is_activity or self.is_optional:
            if not self.fee_structure_id:
                raise UserError(_("Please select 'Fees Structure'"))
        if self.is_transport:
            if not self.fee_structure_id.is_include_transport_fees:
                raise UserError(
                    _("%s is not allow Transport Fee", self.fee_structure_id.name)
                )
        if self.is_activity:
            if not self.fee_structure_id.is_include_activity_fees:
                raise UserError(
                    _("%s is not allow Activity Fee", self.fee_structure_id.name)
                )
        if self.is_optional:
            if not self.fee_structure_id.is_include_optional_fees:
                raise UserError(
                    _("%s is not allow Optional Fee", self.fee_structure_id.name)
                )

    # old field
    fees_to_zone = fields.Many2one(
        "xe.fees.type", string="To Zone", track_visibility="always"
    )
    # new field
    fees_to_zone_id = fields.Many2one(
        "xe.fees.type", string="To Zone", track_visibility="always"
    )
    activity_fee_ids = fields.Many2many("xe.fees.type")
    optional_fee_ids = fields.Many2many(
        "xe.fees.type", "xe_fees_optional_app", "fee_type_id", "optional_id"
    )
    dob = fields.Date(string="Date of Birth")
    # old field
    academic_year = fields.Many2one("xe.academic.year")
    # new field
    academic_year_id = fields.Many2one("xe.academic.year")
    joined_date = fields.Date(default=fields.Date.today())
    remarks = fields.Text()
    email = fields.Char()
    parent_ids = fields.Many2many("xe.parent", string="Parent Details")
    discharge_from_ears = fields.Boolean()
    any_disease_of_eyes = fields.Boolean(string="Any Disease of Eyes")
    hearing_difficulties = fields.Boolean()

    breathlessness = fields.Boolean()
    pain_in_chest = fields.Boolean()
    palpitations = fields.Boolean()
    any_disease_of_heart = fields.Boolean(string="Any Disease of Heart")

    persistant_cough = fields.Boolean()
    any_disease_of_chest = fields.Boolean(string="T.B. or Any Disease of Chest")
    asthma = fields.Boolean()

    worms = fields.Boolean()
    chronic_diarrhoea = fields.Boolean()
    blood_in_stool = fields.Boolean(string="Blood in Stool")

    enuresis = fields.Boolean()
    blood_in_urine = fields.Boolean(string="Blood in Urine")

    state_of_feet_legs = fields.Boolean(string="State of Feet / Legs")
    spinal_deformity = fields.Boolean()
    posture_defect = fields.Boolean()

    scabies = fields.Boolean()
    eczema = fields.Boolean()
    eruptions = fields.Boolean()
    hair_lice = fields.Boolean()

    disorders_of_speech = fields.Boolean(string="Disorders of Speech")
    mental_illness = fields.Boolean()
    personality_disorder = fields.Boolean()
    fits = fields.Boolean(string="FITS")
    mental_subnormality = fields.Boolean()
    allergy_or_reaction = fields.Char(string="Allergy or Reaction")
    any_hereditary_disease = fields.Char()

    weight = fields.Char()
    height = fields.Char()
    skin = fields.Char()
    general_appearance = fields.Char()

    pupils_right = fields.Char()
    far_right = fields.Char()
    near_right = fields.Char()
    color_vision = fields.Char()
    pupils_left = fields.Char()
    far_left = fields.Char()
    near_left = fields.Char()

    canals_right = fields.Char()
    drums_right = fields.Char()
    hearing_right = fields.Char()
    canals_left = fields.Char()
    drums_left = fields.Char()
    hearing_left = fields.Char()

    nose_septum = fields.Char()
    nose_musoca = fields.Char()

    throat_tonsils = fields.Char()
    throat_musoca = fields.Char()

    teeth = fields.Char()
    musoca = fields.Char()
    tongue = fields.Char()

    cardio_vascular = fields.Char(string="Cardiovascular")
    lungs = fields.Char()
    liver = fields.Char()
    pulse_right = fields.Char()
    gastrointestinal = fields.Char()
    spleen = fields.Char()
    heart_sound = fields.Char(string="Heart Sound / Murmer")
    contours = fields.Char()
    hernia = fields.Char()
    repspiratory = fields.Char()
    masses = fields.Char()
    genitourinary = fields.Char()
    back = fields.Char()
    posture = fields.Char()
    extremities = fields.Char()
    deformity = fields.Char()

    motor_system = fields.Char()
    s_g = fields.Char(string="S.G.")
    microscopic = fields.Char()
    eggs_cysts = fields.Char(string="Eggs,Cysts")
    urine_appearance = fields.Char()
    deposits = fields.Char()
    worms_n = fields.Char(string="Worm")
    hbp = fields.Char(string="H.B.P.")
    sensory_system = fields.Char()
    albumin = fields.Char()
    blood = fields.Char()
    reflexes = fields.Char()
    sugar = fields.Char()
    stool = fields.Char()
    blood_level = fields.Char()
    lbp = fields.Char(string="L.B.P.")
    summary_of_positive_findings = fields.Char(string="Summary of Positive Findings")

    doctor_name = fields.Char()
    contact_no = fields.Char()
    cell_no = fields.Char(string="Mobile")
    particular_note = fields.Char(string="Particular Note / Suggestion By Doctor")

    student_birthcert = fields.Binary("Student Birth Certificate")
    store_fname1 = fields.Char("File Name1")

    student_passport = fields.Binary("Student Passport Copy")
    store_fname2 = fields.Char("File Name2")
    father_passport = fields.Binary(
        "Father Passport CopyKenyen Identity Card / Allien Card"
    )
    store_fname3 = fields.Char("File Name3")

    mother_passport = fields.Binary(
        "Mother Passport CopyKenyen Identity Card / Allien Card"
    )
    store_fname4 = fields.Char("File Name4")

    passportcopy_father = fields.Binary("Passport Copy of Father")
    store_fname5 = fields.Char("File Name5")

    passportcopy_mother = fields.Binary("Passport Copy of Mother")
    store_fname6 = fields.Char("File Name6")
    student_pupil_pass = fields.Binary()
    store_fname7 = fields.Char("File Name7")

    dependant_pass = fields.Binary()
    store_fname8 = fields.Char("File Name8")

    previous_term_report = fields.Binary("Previous Term Report Form")
    store_fname9 = fields.Char("File Name9")

    admission_in_first_year = fields.Binary(
        "For Admission In Year 1 Studying In Pre-Primary/ Nursery Class Report"
    )
    store_fname10 = fields.Char("File Name10")

    leaving_certificate = fields.Binary("Previous School Leaving Certificate")
    store_fname11 = fields.Char("File Name11")

    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string="State")
    county = fields.Char()
    zip = fields.Char(string="Postal Code")
    country_id = fields.Many2one("res.country", string="Country")
    fees_term_id = fields.Many2one("xe.fees.term", "Fees Term")
    transportation_term_id = fields.Many2one("xe.fees.term.line", "Transportation Fees")
    image = fields.Binary()
    certificate_number = fields.Char()
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    admission_number = fields.Char()

    @api.model
    def create(self, vals):
        class_admission_no_automatic = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xenesis_school_base.class_admission_no_automatic")
            or False
        )
        result = super(ApplicationForm, self).create(vals)
        return result

    def action_reset_draft(self):
        self.state = "draft"

    def unlink(self):
        for application in self:
            if application.enquiry_id and application.enquiry_id.id:
                raise UserError(
                    _(
                        "You can not delete an Application without deleting its Enquiry First."
                    )
                )
        return super(ApplicationForm, self).unlink()

    def action_cancel(self):
        self.state = "cancelled"

    def action_submit(self):
        self.state = "submitted"

    def get_grouped(self, val):
        from collections import defaultdict

        res = defaultdict(list)
        for v, k in val:
            res[k].append(v)
        result = [{"date": k, "line_ids": v} for k, v in res.items()]
        return result

    def action_view_invoice(self):
        self.ensure_one()
        # student_obj = (
        #     self.env["xe.student"].search([("name", "=", self.student_name), ("company_id", "=", self.company_id.id)])
        # )
        student_obj = (
            self.env["xe.student"].search([("enquiry_id", "=", self.enquiry_id.id), ("company_id", "=", self.company_id.id)], limit=1)
        )
        partner_id = student_obj.partner_id and student_obj.partner_id.id
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        action["domain"] = [
            ("partner_id", "=", partner_id),
        ]
        action["context"] = {"default_partner_id": partner_id}
        return action

    def action_open_student(self):
        form_view = self.env.ref("xenesis_school_base.view_student_form")
        tree_view = self.env.ref("xenesis_school_base.view_student_tree")
        stud_rec = (
            self.env["xe.student"]
            .search([("enquiry_id", "=", self.enquiry_id.id), ("company_id", "=", self.company_id.id)], limit=1)
            .id
        )

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

    def action_enroll(self):
        course_id = self.course_id and self.course_id.id
        classroom_id = self.classroom_id and self.classroom_id.id
        fees_term_obj = self.fees_term_id
        transportation_term_obj = self.transportation_term_id
        course_vals_array = []
        course_vals_array.append(course_id)
        term_id = self.term_id and self.term_id.id
        stream_id = self.stream_id and self.stream_id.id
        course_vals = {}
        if course_id:
            course_vals["course_id"] = course_id
        if classroom_id:
            course_vals["classroom_id"] = classroom_id
        if term_id:
            course_vals["term_id"] = term_id
        if stream_id:
            course_vals["stream_id"] = stream_id

        course_detail_ids = [(0, 0, course_vals)]
        vals = {
            "roll_number": self.admission_number,
            "name": self.student_name,
            "nationality_id": self.nationality_id and self.nationality_id.id,
            "gender": self.gender,
            "dob": self.dob,
            "email": self.email,
            "image_1920": self.image,
            "street": self.street,
            "street2": self.street2,
            "city": self.city,
            "state_id": self.state_id and self.state_id.id,
            "zip": self.zip,
            "country_id": self.country_id and self.country_id.id,
            "course_id": course_id,
            "classroom_id": self.classroom_id and self.classroom_id.id,
            "course_detail_ids": course_detail_ids,
            "application_id": self.id,
            "transportation_term_id": self.transportation_term_id
            and self.transportation_term_id.id,
            "enquiry_id": self.enquiry_id and self.enquiry_id.id or False,
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
            "certificate_number": self.certificate_number,
            "student_birthcert": self.student_birthcert,
            "store_fname1": self.store_fname1,
            "academic_year_id": self.academic_year_id
            and self.academic_year_id.id
            or False,
            "joined_date": self.joined_date,
            "student_ids": (
                [(6, 0, self.enquiry_id.student_ids.ids)]
                if self.enquiry_id.student_ids
                else [(6, 0, [])]
            ),
        }
        # student = (
        #     self.env["xe.student"]
        #     .sudo()
        #     .search([("name", "=", self.student_name)], limit=1)
        # )
        # if not student:
        student = self.env["xe.student"].sudo().create(vals)
        self.create_health_records(student)

        parents = []
        for parent in self.enquiry_id.parent_ids:
            student_parent_vals = {"parent_id": parent.id, "student_id": student.id}
            student_parent_relation = (
                self.env["xe.student.parent"].sudo().create(student_parent_vals)
            )
            for rec in student_parent_relation:
                parents.append(rec.parent_id and rec.parent_id.id)

            student_parent_relation.sudo().write(
                {"course_ids": [(6, 0, course_vals_array)]}
            )

        self.env["xe.student"].browse(student.id).write(
            {
                "parent_ids": [(6, 0, self.enquiry_id.parent_ids.ids)],
                "student_ids": [(6, 0, self.enquiry_id.student_ids.ids)],
            }
        )
        fees_line_vals = self.create_fees_lines(fees_term_obj, transportation_term_obj)

        if student:
            self.env["xe.student"].browse(student.id).write(
                {"fees_detail_line_ids": fees_line_vals}
            )

        # Enroll wizard
        student_id = student.id
        invoice_line_ids = []
        # Add Academic Line
        # fees_academic = (
        #     self.env["xe.fees.structure"]
        #     .sudo()
        #     .search(
        #         [
        #             ("course_id", "=", self.course_id.id),
        #             ("fee_structu_type", "=", "academic"),
        #             ("academic_year", "=", self.academic_year.id),
        #         ]
        #     )
        # )
        fees_academic = self.fee_structure_id
        for fees in fees_academic:
            for line in fees.fee_details_ids:
                inv_line_vals = {
                    "fee_type_id": line.fee_type_id.id,
                    "term_id": line.term_id.id,
                    "amount": line.amount,
                    "invoice_date": line.invoice_date,
                    "due_date": line.due_date,
                    "schedule_date": line.schedule_date,
                    "receipt_name_id": line.receipt_name_id.id,
                    "fee_structure_id": fees_academic.id,
                    "fees_detail_id": line.id,
                    "academic_fee": True,
                }
                invoice_line_ids.append([0, 0, inv_line_vals])
        # Show transport line product
        if self.is_transport:
            if self.fees_to_zone_id:
                inv_line_vals = {
                    "fee_type_id": self.fees_to_zone_id.id,
                    "term_id": self.fee_structure_id.term_id.id,
                    "amount": self.fees_to_zone_id.product_id.list_price,
                    "transport_fee": True,
                    "invoice_date": self.fee_structure_id.invoice_date,
                    "fee_structure_id": fees_academic.id,
                }
                invoice_line_ids.append([0, 0, inv_line_vals])
        # if self.is_transport:
        #     fee_details_line = (
        #         self.env["xe.fees.details"]
        #         .sudo()
        #         .search(
        #             [
        #                 ("fee_type", "=", self.fees_to_zone_id.id),
        #                 ("fee_structure_id.academic_year", "=", self.academic_year.id),
        #             ]
        #         )
        #     )
        #     for line in fee_details_line:
        #         inv_line_vals = {
        #             "fee_type": line.fee_type.id,
        #             "term": line.term.id,
        #             "amount": line.amount,
        #             "invoice_date": line.invoice_date,
        #             "due_date": line.due_date,
        #             "schedule_date": line.schedule_date,
        #             "receipt_name_id": line.receipt_name_id.id,
        #             # "fee_structure_id": fee_details_line.fee_structure_id.id,
        #             "fee_structure_id": fees_academic.id,
        #             "fees_detail_id": line.id,
        #             "transport_fee": True,
        #         }
        #         invoice_line_ids.append([0, 0, inv_line_vals])

        # Show Activity line product
        if self.is_activity:
            if self.activity_fee_ids:
                for line in self.activity_fee_ids:
                    inv_line_vals = {
                        "fee_type_id": line.id,
                        "term_id": self.fee_structure_id.term_id.id,
                        "amount": line.product_id.list_price,
                        "activity_fee": True,
                        "invoice_date": self.fee_structure_id.invoice_date,
                        "fee_structure_id": fees_academic.id,
                    }
                    invoice_line_ids.append([0, 0, inv_line_vals])

        # if self.is_activity:
        #     fees_struc = (
        #         self.env["xe.fees.structure"]
        #         .sudo()
        #         .search(
        #             [
        #                 ("is_activity", "=", self.is_activity),
        #                 ("company_id", "=", self.env.user.company_id.id),
        #                 ("academic_year", "=", self.academic_year.id),
        #             ]
        #         )
        #     )
        #     for fees in fees_struc:
        #         for fees_line in fees.fee_details_ids:
        #             if fees_line.fee_type.fee_type in self.activity_fee_ids.mapped(
        #                 "fee_type"
        #             ):
        #                 inv_line_vals = {
        #                     "fee_type": fees_line.fee_type.id,
        #                     "term": fees_line.term.id,
        #                     "amount": fees_line.amount,
        #                     "invoice_date": fees_line.invoice_date,
        #                     "due_date": fees_line.due_date,
        #                     "schedule_date": fees_line.schedule_date,
        #                     "fee_structure_id": fees_struc.id,
        #                     "receipt_name_id": fees_line.receipt_name_id.id,
        #                     "fees_detail_id": fees_struc.id,
        #                     "activity_fee": True,
        #                 }
        #                 invoice_line_ids.append([0, 0, inv_line_vals])

        # Show Optional line product
        if self.is_optional:
            if self.optional_fee_ids:
                for line in self.optional_fee_ids:
                    inv_line_vals = {
                        "fee_type_id": line.id,
                        "term_id": self.fee_structure_id.term_id.id,
                        "amount": line.product_id.list_price,
                        "optional_fee": True,
                        "invoice_date": self.fee_structure_id.invoice_date,
                        "fee_structure_id": fees_academic.id,
                    }
                    invoice_line_ids.append([0, 0, inv_line_vals])
        # if self.is_optional:
        #     fees_struc = (
        #         self.env["xe.fees.structure"]
        #         .sudo()
        #         .search(
        #             [
        #                 ("is_optional", "=", self.is_optional),
        #                 ("company_id", "=", self.env.user.company_id.id),
        #                 ("academic_year", "=", self.academic_year.id),
        #             ]
        #         )
        #     )
        #     for fees in fees_struc:
        #         for fees_line in fees.fee_details_ids:
        #             if fees_line.fee_type.fee_type in self.optional_fee_ids.mapped(
        #                 "fee_type"
        #             ):
        #                 inv_line_vals = {
        #                     "fee_type": fees_line.fee_type.id,
        #                     "term": fees_line.term.id,
        #                     "amount": fees_line.amount,
        #                     "invoice_date": fees_line.invoice_date,
        #                     "due_date": fees_line.due_date,
        #                     "schedule_date": fees_line.schedule_date,
        #                     "fee_structure_id": fees_struc.id,
        #                     "receipt_name_id": fees_line.receipt_name_id.id,
        #                     "fees_detail_id": fees_struc.id,
        #                     "optional_fee": True,
        #                 }
        #                 invoice_line_ids.append([0, 0, inv_line_vals])

        # Show Boarding line product
        if self.is_boarding:
            fees_struct_rec = (
                self.env["xe.fees.structure"]
                .sudo()
                .search(
                    [
                        ("fee_structu_type", "=", "boarding"),
                        ("course_id", "in", self.course_id.id),
                        ("academic_year_id", "=", self.academic_year_id.id),
                    ]
                )
            )
            if fees_struct_rec:
                fee_details_line = (
                    self.env["xe.fees.details"]
                    .sudo()
                    .search([("fee_structure_id", "=", fees_struct_rec.id)])
                )
                for line in fee_details_line:
                    inv_line_vals = {
                        "fee_type_id": line.fee_type_id.id,
                        "term_id": line.term_id.id,
                        "amount": line.amount,
                        "invoice_date": line.invoice_date,
                        "due_date": line.due_date,
                        "schedule_date": line.schedule_date,
                        "fee_structure_id": fees_struct_rec.id,
                        "receipt_name_id": line.receipt_name_id.id,
                        "fees_detail_id": line.id,
                        "boarding_fee": True,
                    }
                    invoice_line_ids.append([0, 0, inv_line_vals])

        addmission_fees_rec = (
            self.env["admission.fee.wizard"]
            .with_context(student_id=student_id)
            .sudo()
            .create(
                {
                    "student_id": student_id,
                    "is_transport": self.is_transport,
                    "is_activity": self.is_activity,
                    "is_boarding": self.is_boarding,
                    "is_optional": self.is_optional,
                    "course_id": self.course_id.id,
                    "classroom_id": self.classroom_id.id,
                    "current_academic_year_id": self.academic_year_id.id,
                    "fees_to_zone_id": self.fees_to_zone_id.id,
                    "activity_fee_ids": self.activity_fee_ids.ids,
                    "optional_fee_ids": self.optional_fee_ids.ids,
                    "fee_details_ids": invoice_line_ids,
                    "application_id": self.id,
                    "term_id": self.fee_structure_id.term_id.id,
                }
            )
        )
        return {
            "name": _("Admission Fee Wizard"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "admission.fee.wizard",
            "res_id": addmission_fees_rec.id,
            "target": "new",
        }

    def create_fees_lines(self, fees_term_obj, transportation_term_obj):
        final_fee_vals = []
        val = []
        if fees_term_obj:
            for line in fees_term_obj.fees_line:
                date_feesterm_tuple = (line.id, line.start_date)
                val.append(date_feesterm_tuple)
        if transportation_term_obj:
            date_transportationterm_tuple = (
                transportation_term_obj.id,
                transportation_term_obj.start,
            )
            val.append(date_transportationterm_tuple)
        grouped_dict = self.get_grouped(val)
        for rec in grouped_dict:
            fee_termline_ids = rec["line_ids"]
            fee_termline_obj = self.env["xe.fees.term.line"].browse(fee_termline_ids)
            fee_term_ids_array = []
            fee_term_pdt_ids_array = []
            fee_sub_line_ids = []
            date = rec["date"]
            amount = 0
            for li in fee_termline_obj:
                fee_sub_dict = {"fee_term_line_id": li.id}
                fee_sub_line_ids.append((0, 0, fee_sub_dict))
                amount = amount + li.value
                fee_term_ids_array.append(int(li.id))
                fee_term_pdt_ids_array.append(li.product_id and li.product_id.id)
            if not fee_term_pdt_ids_array:
                raise ValidationError(
                    _("Please Fill Description field inside fees term line")
                )
            dict_val = {
                "state": "draft",
                "amount": amount,
                "fees_term_line_ids": [(6, 0, fee_term_ids_array)],
                "product_ids": [(6, 0, fee_term_pdt_ids_array)],
                "date": date,
                "fee_sub_line_ids": fee_sub_line_ids,
            }
            final_fee_vals.append([0, False, dict_val])
        return final_fee_vals

    def create_health_records(self, student):
        date = datetime.now()
        discharge_from_ears = self.discharge_from_ears
        any_disease_of_eyes = self.any_disease_of_eyes
        hearing_difficulties = self.hearing_difficulties
        breathlessness = self.breathlessness
        pain_in_chest = self.pain_in_chest
        palpitations = self.palpitations
        any_disease_of_heart = self.any_disease_of_heart
        persistant_cough = self.persistant_cough
        any_disease_of_chest = self.any_disease_of_chest
        asthma = self.asthma
        worms = self.worms
        chronic_diarrhoea = self.chronic_diarrhoea
        blood_in_stool = self.blood_in_stool
        enuresis = self.enuresis
        blood_in_urine = self.blood_in_urine
        state_of_feet_legs = self.state_of_feet_legs
        spinal_deformity = self.spinal_deformity
        posture_defect = self.posture_defect
        scabies = self.scabies
        eczema = self.eczema
        eruptions = self.eruptions
        hair_lice = self.hair_lice
        disorders_of_speech = self.disorders_of_speech
        mental_illness = self.mental_illness
        personality_disorder = self.personality_disorder
        fits = self.fits
        mental_subnormality = self.mental_subnormality
        allergy_or_reaction = self.allergy_or_reaction
        any_hereditary_disease = self.any_hereditary_disease
        weight = self.weight
        height = self.height
        skin = self.skin
        general_appearance = self.general_appearance
        pupils_right = self.pupils_right
        far_right = self.far_right
        near_right = self.near_right
        color_vision = self.color_vision
        pupils_left = self.pupils_left
        far_left = self.far_left
        near_left = self.near_left
        canals_right = self.canals_right
        drums_right = self.drums_right
        hearing_right = self.hearing_right
        canals_left = self.canals_left
        drums_left = self.drums_left
        hearing_left = self.hearing_left
        nose_septum = self.nose_septum
        nose_musoca = self.nose_musoca
        throat_tonsils = self.throat_tonsils
        throat_musoca = self.throat_musoca
        teeth = self.teeth
        musoca = self.musoca
        tongue = self.tongue
        cardio_vascular = self.cardio_vascular
        lungs = self.lungs
        liver = self.liver
        pulse_right = self.pulse_right
        gastrointestinal = self.gastrointestinal
        spleen = self.spleen
        heart_sound = self.heart_sound
        contours = self.contours
        hernia = self.hernia
        repspiratory = self.repspiratory
        masses = self.masses
        genitourinary = self.genitourinary
        back = self.back
        posture = self.posture
        extremities = self.extremities
        deformity = self.deformity
        motor_system = self.motor_system
        s_g = self.s_g
        microscopic = self.microscopic
        eggs_cysts = self.eggs_cysts
        urine_appearance = self.urine_appearance
        deposits = self.deposits
        worms_n = self.worms_n
        hbp = self.hbp
        sensory_system = self.sensory_system
        albumin = self.albumin
        blood = self.blood
        reflexes = self.reflexes
        sugar = self.sugar
        stool = self.stool
        blood_level = self.blood_level
        lbp = self.lbp
        summary_of_positive_findings = self.summary_of_positive_findings
        remarks = self.remarks
        doctor_name = self.doctor_name
        contact_no = self.contact_no
        cell_no = self.cell_no
        particular_note = self.particular_note
        vals = {
            "checkup_date": date,
            "partner_id": student and student.partner_id and student.partner_id.id,
            "type_record": "s",
            "discharge_from_ears": discharge_from_ears,
            "any_disease_of_eyes": any_disease_of_eyes,
            "hearing_difficulties": hearing_difficulties,
            "breathlessness": breathlessness,
            "pain_in_chest": pain_in_chest,
            "palpitations": palpitations,
            "any_disease_of_heart": any_disease_of_heart,
            "persistant_cough": persistant_cough,
            "any_disease_of_chest": any_disease_of_chest,
            "asthma": asthma,
            "worms": worms,
            "chronic_diarrhoea": chronic_diarrhoea,
            "blood_in_stool": blood_in_stool,
            "enuresis": enuresis,
            "blood_in_urine": blood_in_urine,
            "state_of_feet_legs": state_of_feet_legs,
            "spinal_deformity": spinal_deformity,
            "posture_defect": posture_defect,
            "scabies": scabies,
            "eczema": eczema,
            "eruptions": eruptions,
            "hair_lice": hair_lice,
            "disorders_of_speech": disorders_of_speech,
            "mental_illness": mental_illness,
            "personality_disorder": personality_disorder,
            "fits": fits,
            "mental_subnormality": mental_subnormality,
            "allergy_or_reaction": allergy_or_reaction,
            "any_hereditary_disease": any_hereditary_disease,
            "weight": weight,
            "height": height,
            "skin": skin,
            "general_appearance": general_appearance,
            "pupils_right": pupils_right,
            "far_right": far_right,
            "near_right": near_right,
            "color_vision": color_vision,
            "pupils_left": pupils_left,
            "far_left": far_left,
            "near_left": near_left,
            "canals_right": canals_right,
            "drums_right": drums_right,
            "hearing_right": hearing_right,
            "canals_left": canals_left,
            "drums_left": drums_left,
            "hearing_left": hearing_left,
            "nose_septum": nose_septum,
            "nose_musoca": nose_musoca,
            "throat_tonsils": throat_tonsils,
            "throat_musoca": throat_musoca,
            "teeth": teeth,
            "musoca": musoca,
            "tongue": tongue,
            "cardio_vascular": cardio_vascular,
            "lungs": lungs,
            "liver": liver,
            "pulse_right": pulse_right,
            "gastrointestinal": gastrointestinal,
            "spleen": spleen,
            "heart_sound": heart_sound,
            "contours": contours,
            "hernia": hernia,
            "repspiratory": repspiratory,
            "masses": masses,
            "genitourinary": genitourinary,
            "back": back,
            "posture": posture,
            "extremities": extremities,
            "deformity": deformity,
            "motor_system": motor_system,
            "s_g": s_g,
            "microscopic": microscopic,
            "eggs_cysts": eggs_cysts,
            "urine_appearance": urine_appearance,
            "deposits": deposits,
            "worms_n": worms_n,
            "hbp": hbp,
            "sensory_system": sensory_system,
            "albumin": albumin,
            "blood": blood,
            "reflexes": reflexes,
            "sugar": sugar,
            "stool": stool,
            "blood_level": blood_level,
            "lbp": lbp,
            "summary_of_positive_findings": summary_of_positive_findings,
            "remarks": remarks,
            "doctor_name": doctor_name,
            "contact_no": contact_no,
            "cell_no": cell_no,
            "particular_note": particular_note,
        }
        self.env["xe.medicalcheckup"].sudo().create(vals)
