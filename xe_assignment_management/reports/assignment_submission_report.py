from odoo import api, models


class StudentAssignmentSubmission(models.AbstractModel):
    _name = "report.xe_assignment_management.report_assignment_submit"
    _description = "Assignment Management Assignment Submit Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        from_date = data["from_date"]
        to_date = data["to_date"]
        course_id = data["course_id"]
        state = data["state"]
        submission_obj = self.env["xe.assignment.submission"]
        domain = []
        if from_date:
            domain.append(("submit_date", ">=", from_date))
        if to_date:
            domain.append(("submit_date", "<=", to_date))
        if course_id:
            domain.append(("assignment_id.course_id", "=", course_id))
        if state:
            domain.append(("state", "=", state))
        else:
            domain.append(("state", "not in", ["cancel", "draft"]))
        docs = submission_obj.search(domain)
        docids = docs.ids
        return {
            "doc_ids": docids,
            "doc_model": "xe.assignment.submission",
            "docs": docs,
            "data": data,
        }
