from odoo import models, fields, api, _


class XeStudent(models.Model):
    _inherit = "xe.student"

    def action_create_marking(self):
        rubrics = self.env["xe.rubric"].search([])
        subject_obj = self.env["xe.subject"]
        mark_obj = self.env["xe.marking"]

        for student in self:
            # subjects = student.subjects  # Assuming student has a One2many field 'subject_ids' linking to subjects taken
            subjects = subject_obj.search(
                [("course_ids", "in", [student.course_id.id])]
            )
            for subject in subjects:
                rubrics_for_subject = rubrics.filtered(
                    lambda r: r.subject_id.id == subject.id
                )
                for rubric in rubrics_for_subject:
                    existing_record = mark_obj.search(
                        [("student_id", "=", student.id), ("rubric_id", "=", rubric.id)]
                    )
                    if not existing_record:
                        mark_obj.create(
                            {
                                "student_id": student.id,
                                "rubric_id": rubric.id,
                                "rubric_activity": rubric.activity,
                                "grade": "",  # Set the default grade as 'EE', change it as needed
                            }
                        )


class XeSubject(models.Model):
    _inherit = "xe.subject"

    is_theme = fields.Boolean(default=True)
    theme_ids = fields.One2many("xe.theme", "subject_id")
    strand_ids = fields.One2many("xe.strand", "subject_id")
