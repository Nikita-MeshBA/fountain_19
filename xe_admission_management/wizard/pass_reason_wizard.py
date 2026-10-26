from odoo import api, fields, models


class PassOrFailReason(models.TransientModel):
    _name = "pass.or.fail.reason"
    _description = "Reason Capture for Pass or Fail"

    description = fields.Text(string="Notes", required=True)
    student_name = fields.Char(readonly=True)
    interview_start_date = fields.Datetime(string="Interview Start", readonly=True)
    interview_end_date = fields.Datetime(string="Interview End", readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(PassOrFailReason, self).default_get(fields)
        active_ids = self.env.context.get("active_ids", []) or []
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)

        res.update(
            {
                "interview_start_date": admission_obj.interview_start_date,
                "interview_end_date": admission_obj.interview_end_date,
                "student_name": admission_obj.name,
            }
        )
        return res

    def action_ok(self):
        active_ids = self.env.context.get("active_ids", []) or []
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)
        result = self.env.context.get("default_result")
        if result == "pass":
            admission_obj.write({"pass_reason": self.description, "state": "passed"})
        else:
            admission_obj.write({"fail_reason": self.description, "state": "failed"})
