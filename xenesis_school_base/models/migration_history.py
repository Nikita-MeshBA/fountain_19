from odoo import fields, models


class MigrationHistory(models.Model):
    _name = "xe.migration.history"
    _inherit = ["mail.thread"]
    _description = "Migration History"
    _rec_name = "student_id"

    date = fields.Date()
    student_id = fields.Many2one("xe.student")
    from_course_id = fields.Many2one("xe.course", string="From Class")
    from_term_id = fields.Many2one("xe.term")
    to_course_id = fields.Many2one("xe.course", string="To Class")
    to_term_id = fields.Many2one("xe.term")
    remarks = fields.Text()
    user_id = fields.Many2one("res.users")
    # old field
    from_academic_yr = fields.Many2one("xe.academic.year", "From Academic Year")
    # new field
    from_academic_yr_id = fields.Many2one("xe.academic.year", "From Academic Year")
    # old field
    to_academic_yr = fields.Many2one("xe.academic.year", "To Academic Year")
    # new field
    to_academic_yr_id = fields.Many2one("xe.academic.year", "To Academic Year")
    from_company_id = fields.Many2one("res.company")
    to_company_id = fields.Many2one("res.company")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    from_classroom_id = fields.Many2one("xe.classroom")
    to_classroom_id = fields.Many2one("xe.classroom")
