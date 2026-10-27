from odoo.exceptions import UserError

from odoo import models, fields, _


class XeMarkingWizard(models.TransientModel):
    _name = "xe.marking.wizard"
    _description = "Marking Summary Wizard"

    academic_term_id = fields.Many2one("xe.academic.terms")
    course_id = fields.Many2one("xe.course")
    classroom_id = fields.Many2one(
        "xe.classroom", domain="[('course_id', '=', course_id)]"
    )
    subject_id = fields.Many2one(
        "xe.subject", domain="[('course_ids', 'in', [course_id])]"
    )
    marking_wizard_line_ids = fields.One2many(
        "xe.marking.wizard.line", "marking_wizard_id"
    )

    # # When a record is created by a user unlinks(deletes) previous records made by same user. This is to ensure no repeated/overlapping results.
    # @api.model
    # def create(self, vals):
    #     existing_records = self.search([('create_uid', '=', self.env.user.id)])
    #     existing_records.unlink()
    #     return super(XeMarkingWizard, self).create(vals)

    # Generates records to be sent to other model for viewing based on given criteria.
    def generate_summary(self):
        # teacher = self.subject.class_teacher.user_id
        # if not self.env.user.has_group('T_Student.school_admin_access'):
        #     if self.env.user.id not in teacher.ids:
        #         raise UserError("The selected subject does not belong to you.") # Error message if user not admin and not subject teacher

        # Matches given search criteria in the student.marking model
        domain = [
            ("course_id", "=", self.course_id.id),
            ("academic_term_id", "=", self.academic_term_id.id),
            ("subject_id", "=", self.subject_id.id),
        ]
        if self.classroom_id:
            domain.append(("classroom_id", "=", self.classroom_id.id))
        marking_ids = self.env["xe.marking"].search(domain)

        unique_students = marking_ids.mapped("student_id")
        marking_lines = []
        for student in unique_students:
            marking_wizard_line_ids = self.env["xe.marking.wizard.line"].search(
                domain + [("student_id", "=", student.id)]
            )
            if marking_wizard_line_ids:
                marking_wizard_line_ids.unlink()

            student_marking_ids = marking_ids.filtered(
                lambda l: l.student_id == student
            )
            marking_lines.append(
                (
                    0,
                    0,
                    {
                        "student_id": student.id,
                        "academic_term_id": self.academic_term_id.id,
                        "course_id": self.course_id.id,
                        "classroom_id": self.classroom_id.id,
                        "subject_id": self.subject_id.id,
                        "marking_wizard_id": self.id,
                        "marking_ids": [(6, 0, student_marking_ids.ids)],
                    },
                )
            )

        if not marking_lines:
            raise UserError(
                _("There are no students matching that criteria!")
            )  # Error message if no search results

        self.write({"marking_wizard_line_ids": marking_lines})  # Updates data

        # Returns details for the view
        return {
            "name": "Marking Summary",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "xe.marking.wizard.line",
            "type": "ir.actions.act_window",
            "target": "current",
        }


class XeMarkingWizardLine(models.TransientModel):
    _name = "xe.marking.wizard.line"
    _description = "Marking Summary Line"

    marking_wizard_id = fields.Many2one("xe.marking.wizard", ondelete="cascade")
    student_id = fields.Many2one("xe.student")
    academic_term_id = fields.Many2one("xe.academic.terms")
    course_id = fields.Many2one("xe.course")
    classroom_id = fields.Many2one("xe.classroom")
    subject_id = fields.Many2one("xe.subject")
    marking_ids = fields.Many2many(
        "xe.marking", default=lambda self: self._default_markings()
    )
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user.id)

    #     # When record is created make sure,, it matches the default rubric function
    #     @api.model
    #     def create(self, vals):
    #         record = super(XeMarkingWizardLine, self).create(vals)
    #         record.rubric_activities = record._default_markings()
    #         return record

    #     # Sets up function for default values (gets values that match search criteria)
    def _default_markings(self):
        domain = [
            ("subject_id", "=", self.subject_id.id),
            ("academic_term_id", "=", self.academic_term_id.id),
            ("course_id", "=", self.course_id.id),
        ]
        if self.classroom_id:
            domain.append(
                ("classroom_id", "=", self.classroom_id.id),
            )
        return self.env["xe.marking"].search(domain)


#     # Function for report generation
#     def print_marking_summary(self):
#         return self.env.ref('T_Student.student_report_gen').report_action(self)
