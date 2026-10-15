from odoo import api, fields, models


class StudentInformationReportWizard(models.TransientModel):
    _name = "xe.student.information.report.wizard"
    _description = "Student Information Report Wizard"

    @api.onchange("course_condition")
    def course_condition_change(self):
        course_ids = []
        if self.course_condition == "all":
            course_obj = self.env["xe.course"].search([])
            for course in course_obj:
                course_ids.append(course.id)
            self.course_ids = [(6, 0, course_ids)]
        else:
            self.course_ids = [(6, 0, course_ids)]

    @api.onchange("term_condition")
    def term_condition_change(self):
        classroom_ids = []
        if self.term_condition == "all":
            classroom_obj = self.env["xe.classroom"].search([])
            for classroom in classroom_obj:
                classroom_ids.append(classroom.id)
            self.class_room_ids = [(6, 0, classroom_ids)]
        else:
            self.class_room_ids = [(6, 0, classroom_ids)]

    fees_filter = fields.Selection(
        [("classroom", "Classroom"), ("course", "Class")],
        default="course",
        string="Options",
        required=True,
    )

    course_ids = fields.Many2many("xe.course", string="Select Class")

    course_condition = fields.Selection(
        [
            ("all", "All"),
            ("course_wise", "Class Wise"),
        ],
        string="Class",
        default="all",
    )

    term_condition = fields.Selection(
        [
            ("all", "All"),
            ("term_wise", "Class Room Wise"),
        ],
        string="Term",
        default="all",
    )

    class_room_ids = fields.Many2many("xe.classroom", string="Select Class Room")
    term_ids = fields.Many2many("xe.term", string="Select Term")
    course = fields.Char()
    classroom = fields.Char()

    def check_report(self):
        data = {}
        if self.course_condition == "all":
            self.course = "All"
        else:
            self.course = self.course_ids.name

        if self.term_condition == "all":
            self.classroom = "All"
        else:
            self.classroom = self.class_room_ids.name

        data["form"] = self.read(
            ["course_ids", "class_room_ids", "course", "classroom", "fees_filter"]
        )[0]
        return (
            self.env.ref("xenesis_school_base.action_report_student_information")
            .with_context(landscape=False)
            .report_action(self, data=data)
        )

    def check_report_xls(self):
        data = {}
        if self.course_condition == "all":
            self.course = "All"
        else:
            self.course = self.course_ids.name

        if self.term_condition == "all":
            self.classroom = "All"
        else:
            self.classroom = self.class_room_ids.name
        data["form"] = self.read(
            ["course_ids", "class_room_ids", "course", "classroom", "fees_filter"]
        )[0]
        return self.env.ref(
            "xenesis_school_base.student_information_xlsx_report"
        ).report_action(self, data=data)
