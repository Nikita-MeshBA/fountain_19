from odoo import models, fields, api


class LessonPlanReportWizard(models.TransientModel):
    _name = "lesson.plan.report.wizard"
    _description = "lesson.plan.report.wizard"

    fees_filter = fields.Selection(
        [
            ("employee", "Employee"),
            ("department", "Department"),
            ("classroom", "Classroom"),
            ("course", "Class"),
        ],
        required=True,
    )
    employee_id = fields.Many2one("hr.employee", "Employee")
    department_id = fields.Many2one("hr.department", "Department")
    course_id = fields.Many2one("xe.course", "Class")
    class_room_id = fields.Many2one("xe.classroom", string="Classroom")
    date_from = fields.Date(default=fields.Date.today())
    date_to = fields.Date(default=fields.Date.today())
    all_courses = fields.Selection(
        [("all", "All"), ("select_course", "Class Wise")], default="all", string="Class"
    )

    @api.onchange("all_courses", "fees_filter")
    def set_courses(self):
        for r in self:
            if r.fees_filter != "course":
                r.all_courses = "all"
            r.course_id = False
            r.employee_id = False
            r.class_room_id = False

    def check_report(self):
        data = {}
        if self.fees_filter == "employee":
            data["fees_filter"] = self.fees_filter
            data["employee"] = self.employee_id.id
        elif self.fees_filter == "department":
            data["fees_filter"] = self.fees_filter
            data["department"] = self.department_id.id
        elif self.fees_filter == "classroom":
            data["fees_filter"] = self.fees_filter
            data["classroom"] = self.class_room_id.id
            data["classroom_name"] = self.class_room_id.name
        elif self.fees_filter == "course":
            data["fees_filter"] = self.fees_filter
            if self.course_id.id:
                data["course"] = self.course_id.ids
                data["course_name"] = self.course_id.name
            else:
                data["course"] = self.env["xe.course"].search([]).ids
                data["course_name"] = "All"
        data["date_from"] = self.date_from
        data["date_to"] = self.date_to
        return (
            self.env.ref("xe_lesson_planner.action_scheme_of_work_report")
            .with_context(landscape=True)
            .report_action(self, data=data)
        )

    def check_report_xls(self):
        report_name = "Scheme Of Work Report"
        data = {}
        if self.fees_filter == "employee":
            data["fees_filter"] = self.fees_filter
            data["employee"] = self.employee_id.id
        elif self.fees_filter == "department":
            data["fees_filter"] = self.fees_filter
            data["department"] = self.department_id.id
        elif self.fees_filter == "classroom":
            data["fees_filter"] = self.fees_filter
            data["classroom"] = self.class_room_id.id
            data["classroom_name"] = self.class_room_id.name
        elif self.fees_filter == "course":
            data["fees_filter"] = self.fees_filter
            if self.course_id.id:
                data["course"] = self.course_id.ids
                data["course_name"] = self.course_id.name
            else:
                data["course"] = self.env["xe.course"].search([]).ids
                data["course_name"] = "All"
        data["date_from"] = self.date_from
        data["date_to"] = self.date_to
        data["report_name"] = report_name
        data["company"] = self.env.company.id

        return self.env.ref(
            "xe_lesson_planner.xlsx_scheme_of_work_report"
        ).report_action(self, data=data)
