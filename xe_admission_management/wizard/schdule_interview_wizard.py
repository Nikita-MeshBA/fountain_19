from odoo.exceptions import UserError

from odoo import api, fields, models, _


class ScheduleInterview(models.TransientModel):
    _name = "xe.schedule.interview"
    _description = "Schedule Interview"
    _rec_name = "student_name"

    @api.model
    def default_get(self, fields):
        res = super(ScheduleInterview, self).default_get(fields)
        active_ids = self.env.context.get("active_ids", []) or []
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)
        teacher_email = (
            admission_obj.assigned_id.work_email
            if admission_obj.assigned_id.work_email
            else ""
        )
        student_name = admission_obj.name
        if not teacher_email:
            raise UserError(_("No emails found inside Assign To"))
        student_email = admission_obj.email
        all_emails = ""
        if student_email:
            all_emails += student_email
        if teacher_email:
            all_emails += "," + teacher_email
        parent_emails = ""
        for e in admission_obj.parent_ids:
            if e.email:
                parent_emails = parent_emails + e.email

        if parent_emails:
            all_emails = all_emails + parent_emails
        interview_start_date = admission_obj.interview_start_date or False
        interview_end_date = admission_obj.interview_end_date or False
        description = admission_obj.description
        if admission_obj.assigned_id:
            partner_id = (
                self.env["res.partner"]
                .sudo()
                .search([("name", "=", admission_obj.assigned_id.name)], limit=1)
                .id
            )
        else:
            partner_id = False
        res.update(
            {
                "interview_start_date": interview_start_date,
                "interview_end_date": interview_end_date,
                "description": description,
                "all_email": all_emails,
                "subject": "Interview Scheduled",
                "partner_id": partner_id,
                "student_name": student_name,
            }
        )
        return res

    @api.onchange("interview_start_date")
    def _onchange_interview_start_date(self):
        active_ids = self.env.context.get("active_ids", []) or []
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)
        admission_obj.interview_start_date = self.interview_start_date or False

    @api.onchange("interview_end_date")
    def _onchange_interview_end_date(self):
        active_ids = self.env.context.get("active_ids", []) or []
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)

        admission_obj.interview_end_date = self.interview_end_date or False

    @api.onchange("description")
    def _onchange_description(self):
        active_ids = self.env.context.get("active_ids", []) or []
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)
        admission_obj.description = self.description

    def send_email(self):
        active_ids = self.env.context.get("active_ids", []) or []
        template = self.env.ref(
            "xe_admission_management.mail_template_interview_schedule_new1"
        )
        template.send_mail(self.id, force_send=True)
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)
        des_string = "Interview Scheduled for the Student" + ":" + admission_obj.name
        partner_id = (
            admission_obj.assigned_id
            and admission_obj.assigned_id.user_id
            and admission_obj.assigned_id.user_id.partner_id
            and admission_obj.assigned_id.user_id.partner_id.id
            or False
        )
        if partner_id:
            self.env["calendar.event"].create(
                {
                    "name": des_string,
                    "start_date": self.interview_start_date,
                    "stop_date": self.interview_end_date,
                    "description": des_string,
                    "partner_id": partner_id,
                    "partner_ids": [(6, 0, [partner_id])],
                }
            )
        admission_obj.state = "interview_scheduled"

    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    partner_id = fields.Many2one("res.partner", "Partner")
    interview_start_date = fields.Datetime(string="Interview Start")
    interview_end_date = fields.Datetime(string="Interview End")
    description = fields.Text(string="Notes")
    subject = fields.Char()
    all_email = fields.Char(string="All email")
    student_name = fields.Char()
