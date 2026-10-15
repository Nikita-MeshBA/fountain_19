from odoo import api, fields, models


class StudentMigrationWizard(models.TransientModel):
    _name = "xe.student.migration.wizard"
    _description = "Student Migration Wizard"

    from_course_id = fields.Many2one("xe.course", string="From Class", required=True)
    from_term_id = fields.Many2one("xe.term", string="From Term")
    to_course_id = fields.Many2one("xe.course", string="To Class", required=True)
    to_term_id = fields.Many2one("xe.term")
    student_ids = fields.Many2many("xe.student", string="Students")
    date = fields.Date(default=fields.Date.today())
    from_academic_yr_id = fields.Many2one("xe.academic.year", "From Academic Year")
    to_academic_yr_id = fields.Many2one("xe.academic.year", "To Academic Year")
    from_company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company
    )
    to_company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company
    )
    from_classroom_id = fields.Many2one("xe.classroom")
    to_classroom_id = fields.Many2one("xe.classroom")

    @api.onchange("from_course_id", "from_academic_yr_id", "from_classroom_id")
    def _set_domains(self):
        domain = {}
        domain_val = []
        if self.from_course_id:
            domain_val.append(("course_id", "=", self.from_course_id.id))
        if self.from_academic_yr_id:
            domain_val.append(("current_academic_year_id", "=", self.from_academic_yr_id.id))
        if self.from_classroom_id:
            domain_val.append(("classroom_id", "=", self.from_classroom_id.id))
        domain["student_ids"] = domain_val
        return {"domain": domain}

    @api.onchange("to_classroom_id")
    def _set_students(self):
        domain = []
        if self.from_course_id:
            domain.append(("course_id", "=", self.from_course_id.id))
        if self.from_academic_yr_id:
            domain.append(("current_academic_year_id", "=", self.from_academic_yr_id.id))
        if self.from_classroom_id:
            domain.append(("classroom_id", "=", self.from_classroom_id.id))
        if domain:
            students = self.env["xe.student"].search(domain)
            if students:
                self.write({"student_ids": [(6, 0, students.ids)]})

    def fetch_students(self):
        domain = []
        if self.from_course_id:
            domain.append(("course_id", "=", self.from_course_id.id))
        if self.from_academic_yr_id:
            domain.append(("current_academic_year_id", "=", self.from_academic_yr_id.id))
        if self.from_classroom_id:
            domain.append(("classroom_id", "=", self.from_classroom_id.id))
        students = self.env["xe.student"].search(domain)
        if students:
            self.write({"student_ids": [(6, 0, students.ids)]})

    def action_forward(self):
        activity_type = self.env.ref("xenesis_school_base.activity_type_1")
        for record in self:
            from_course_id = record.from_course_id and record.from_course_id.id
            from_classroom_id = record.from_classroom_id and record.from_classroom_id.id
            to_course_id = record.to_course_id and record.to_course_id.id
            to_classroom_id = record.to_classroom_id and record.to_classroom_id.id
            for stud in record.student_ids:
                migration_vals = {
                    "date": record.date,
                    "from_course_id": from_course_id,
                    "from_classroom_id": from_classroom_id,
                    "to_course_id": to_course_id,
                    "to_classroom_id": to_classroom_id,
                    "from_academic_yr_id": record.from_academic_yr_id.id,
                    "to_academic_yr_id": record.to_academic_yr_id.id,
                    "from_company_id": record.from_company_id.id,
                    "to_company_id": record.to_company_id.id,
                    "remarks": stud.remarks,
                    "user_id": self._uid,
                    "student_id": stud.id,
                }

                staff_id = (
                    self.env["hr.employee"].search(
                        [("user_id", "=", self._uid)], limit=1
                    )
                    and self.env["hr.employee"]
                    .search([("user_id", "=", self._uid)], limit=1)
                    .id
                    or False
                )

                activity_vals = {
                    "date": record.date,
                    "description": "Migration From "
                    + record.from_course_id.name
                    + " to "
                    + record.to_course_id.name,
                    "type_id": activity_type.id,
                    "student_id": stud.id,
                    "teacher_id": staff_id,
                }
                self.env["xe.migration.history"].create(migration_vals)
                self.env["xe.activity"].create(activity_vals)
                course_term_line = (
                    self.env["xe.student.course"].search(
                        [
                            ("course_id", "=", from_course_id),
                            ("classroom_id", "=", from_classroom_id),
                            ("student_id", "=", stud.id),
                        ]
                    )
                    and self.env["xe.student.course"].search(
                        [
                            ("course_id", "=", from_course_id),
                            ("classroom_id", "=", from_classroom_id),
                            ("student_id", "=", stud.id),
                        ]
                    )[0]
                )
                course_term_line.write(
                    {"course_id": to_course_id, "classroom_id": to_classroom_id}
                )
                stud.write(
                    {
                        "course_id": to_course_id,
                        "classroom_id": to_classroom_id,
                        "current_academic_year_id": record.to_academic_yr_id.id,
                        "company_id": record.to_company_id.id,
                    }
                )
                if stud.partner_id.company_id.id != record.to_company_id.id:
                    partner_vals = {
                        "name": stud.partner_id.name,
                        "category_id": [(6, 0, stud.partner_id.category_id.ids)],
                        "company_id": record.to_company_id.id,
                        "property_account_receivable_id": False,
                        "property_account_payable_id": False,
                    }

                    partner = self.env["res.partner"].create(partner_vals)
                    stud.write({"partner_id": partner.id})
                    parents = stud.parent_ids
                    if parents:
                        for parent in parents:
                            partner_vals = {
                                "name": parent.partner_id.name,
                                "mobile": parent.partner_id.mobile,
                                "email": parent.partner_id.email,
                                "category_id": [
                                    (6, 0, parent.partner_id.category_id.ids)
                                ],
                                "company_id": record.to_company_id.id,
                                "property_account_receivable_id": False,
                                "property_account_payable_id": False,
                            }
                            partner = self.env["res.partner"].create(partner_vals)
                            parent.write(
                                {
                                    "company_id": record.to_company_id.id,
                                    "partner_id": partner.id,
                                }
                            )
        return True
