from odoo.exceptions import ValidationError

from odoo import api, fields, models, _


class MedicalCheckup(models.Model):
    _name = "xe.medicalcheckup"
    _description = "Medical Checkup"

    name = fields.Char(default="NEW")
    checkup_date = fields.Datetime()
    next_date = fields.Datetime(string="Next Checkup Date")
    partner_id = fields.Many2one("res.partner", ondelete="cascade")
    type_record = fields.Selection(
        [
            ("t", "Teacher"),
            ("s", "Student"),
            ("o", "Other"),
        ],
        string="Type",
    )
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
    worms_n = fields.Char(string='Worm"s"')
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
    remarks = fields.Char()
    doctor_name = fields.Char()
    contact_no = fields.Char()
    cell_no = fields.Char(string="Cell (M) No")
    particular_note = fields.Char(string="Particular Note/ Suggestion By Doctor")
    student_birthcert = fields.Binary("Student Birth Certificates")
    student_birthcert_name = fields.Char("Student Birth Certificate")
    student_passport = fields.Binary("Student Passport Copy")
    student_passport_name = fields.Char("Student Passport")
    father_passport = fields.Binary(
        "Father Passport Copy Kenyen Identity Card / Allien Card"
    )
    father_passport_name = fields.Char(
        "Father Passport Copy Kenyen Identity Card / Allien Card"
    )

    mother_passport = fields.Binary(
        "Mother Passport Copy Kenyen Identity Card / Allien Card"
    )
    mother_passport_name = fields.Char(
        "Mother Passport Copy Kenyen Identity Card / Allien Card"
    )
    passportcopy_father = fields.Binary("Father Passport Copy")
    passportcopy_father_name = fields.Char("Passport Copy of Father")
    passportcopy_mother = fields.Binary("Mother Passport Copy")
    passportcopy_mother_name = fields.Char("Passport Copy of Mother")
    student_pupil_pass = fields.Binary("Student Pupil")
    student_pupil_pass_name = fields.Char("Student Pupil Pass")
    dependant_pass = fields.Binary()
    dependant_pass_name = fields.Char()
    previous_term_report = fields.Binary()
    previous_term_report_name = fields.Char()
    admission_in_first_year = fields.Binary(
        "For Admission In Year 1 Studying In Pre-Primary/ Nursery Class Report"
    )
    admission_in_first_year_name = fields.Char(
        "For Admission in Year 1 Studying In Pre-Primary/ Nursery Class Report"
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        seq = ""
        if vals.get("name", "New") == "New":
            seq_date = None
            if "create_date" in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals["create_date"])
                )
            seq = (
                self.env["ir.sequence"].next_by_code(
                    "xe.medicalcheckup", sequence_date=seq_date
                )
                or "/"
            )
        result = super(MedicalCheckup, self).create(vals)
        student = self.env["xe.student"].search(
            [("partner_id", "=", result.partner_id.id)]
        )
        if student.roll_number:
            result.name = "HEALTH/" + student.roll_number + "/" + seq
        else:
            result.name = "HEALTH/" + seq
        return result

    @api.constrains("checkup_date")
    def _xe_check_date(self):
        for record in self:
            if record.checkup_date.date() > fields.Date.today():
                raise ValidationError(_("Checkup Date will not be greater than today"))

    @api.onchange("partner_id")
    def partner_id_change(self):
        partner_id = self.partner_id and self.partner_id.id or False
        if partner_id:
            student = self.env["xe.student"].search([("partner_id", "=", partner_id)])
            teacher = self.env["hr.employee"].search([("partner_id", "=", partner_id)])
            if student:
                self.type_record = "s"
            elif teacher:
                self.type_record = "t"
            else:
                self.type_record = "o"
