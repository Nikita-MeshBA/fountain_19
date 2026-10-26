from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class GradeCategory(models.Model):
    _name = "xe.grade.category"

    name = fields.Char()
    course_ids = fields.Many2many("xe.course", "Class")
    subject_ids = fields.Many2many("xe.subject")
    grade_category_line_ids = fields.One2many("xe.grade.category.line", "grade_category_id")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        self.check_category_exists(vals)
        if not vals.get("grade_category_line_ids", False):
            raise ValidationError(_("Atleast one subject need to be configure."))
        return super(GradeCategory, self).create(vals)

    def write(self, vals):
        self.check_category_exists(vals)
        return super(GradeCategory, self).write(vals)

    def check_category_exists(self, vals):
        grade_category_ids = self.search([])
        course_ids = []
        subject_ids = []
        if vals.get("course_ids"):
            course_ids += [course[1] for course in vals.get("course_ids")]
        if vals.get("subject_ids"):
            subject_ids += [subject[1] for subject in vals.get("subject_ids")]

        for category in grade_category_ids:
            if any((True for x in category.mapped("course_ids").ids if x in course_ids)):
                for sub in subject_ids:
                    if sub in category.mapped("subject_ids").ids:
                        subject_id = self.env["xe.subject"].browse(sub)
                        raise ValidationError(_("'%s' subject has already been added under %s" % (subject_id.name, category.name)))

    @api.onchange("course_ids")
    def _onchange_course_ids(self):
        if self.course_ids:
            subject_ids = self.env["xe.subject"].search([("course_ids", "in", self.course_ids.ids)])
            self.subject_ids = [(6, 0, subject_ids.ids)]
        else:
            self.subject_ids = False

class GradeCategoryLine(models.Model):
    _name = "xe.grade.category.line"

    min_per = fields.Integer("Minimum Percentage")
    max_per = fields.Integer("Maximum Percentage")
    result = fields.Char("Result to Display")
    points = fields.Char()
    grade_category_id = fields.Many2one("xe.grade.category")

    @api.constrains("min_per", "max_per")
    def _validate_percentage(self):
        for record in self:
            if record.max_per > 100:
                raise ValidationError(_("Enter proper Percentage!"))
            if record.min_per > record.max_per:
                raise ValidationError(
                    _('"Maximum Percentage" must be greater than "Minimum Percentage"')
                )
