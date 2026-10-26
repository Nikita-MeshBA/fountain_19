import datetime

from odoo import models, fields


class AssignmentSubmissionWizard(models.TransientModel):
    _name = "submission.report.wizard"
    _description = "Submission Report Wizard"

    name = fields.Char(
        "Assignment Submission Report", default="Assignment Submission Report"
    )
    from_date = fields.Date("Start Date", default=datetime.date.today())
    to_date = fields.Date("End Date", default=datetime.date.today())
    course_id = fields.Many2one("xe.course", "Class")
    state = fields.Selection(
        [
            ("submitted", "Submitted"),
            ("late_submit", "Late Submit"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        string="Status",
    )

    def print_report(self):
        data = {
            "from_date": self.from_date,
            "to_date": self.to_date,
            "course_id": self.course_id.id,
            "course": self.course_id.name,
            "state": self.state,
        }
        if self.state:
            state_name = dict(
                self.fields_get(allfields=["state"])["state"]["selection"]
            )[self.state]
            data["state_name"] = state_name
        else:
            data["state_name"] = False
        return self.env.ref(
            "xe_assignment_management.action_asgnmnt_submsn"
        ).report_action(None, data=data)
