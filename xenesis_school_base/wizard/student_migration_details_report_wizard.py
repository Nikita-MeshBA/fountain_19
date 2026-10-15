from odoo import api, fields, models


class StudentMigrationReportWizard(models.TransientModel):
    _name = "xe.student.migration.report.wizard"
    _description = "Student Migration Details Report Wizard"

    @api.onchange("migration_filter")
    def course_condition_change(self):
        if self.migration_filter:
            self.student_id = False
            self.term_id = False
            self.course_id = False

    migration_filter = fields.Selection(
        [("student", "Student"), ("course", "Class"), ("term", "Term")],
        "Filter",
        required=True,
    )
    student_id = fields.Many2one("xe.student")
    course_id = fields.Many2one("xe.course", "Class")
    term_id = fields.Many2one("xe.term")
    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)

    def check_report(self):
        data = {}
        data["form"] = self.read(
            ["student_id", "course_id", "term_id", "date_from", "date_to"]
        )[0]

        return (
            self.env.ref("xenesis_school_base.action_report_student_migration")
            .with_context(landscape=False)
            .report_action(self, data=data)
        )
