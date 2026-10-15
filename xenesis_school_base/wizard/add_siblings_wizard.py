from odoo import fields, models


class AddSiblingsWizard(models.TransientModel):
    _name = "add.siblings.wizard"
    _description = "Siblings Wizard"

    student_id = fields.Many2one("xe.student", readonly=True)
    sibling_ids = fields.Many2many("xe.student")

    def action_ok(self):
        if self.student_id:
            current_student_rec = self.student_id
            current_student_sibling_records = (
                self.env["xe.student"]
                .sudo()
                .search([("id", "in", self.sibling_ids.ids)])
            )
            student_records = current_student_rec + current_student_sibling_records
            # Sibling Records
            sibling_rec = student_records

            studentss = []
            for s in current_student_sibling_records:
                studentss.append(s.id)

            latest_student = studentss
            for i in sibling_rec:
                if i.id in latest_student:
                    latest_student.remove(i.id)
                i.student_ids = [(6, 0, latest_student)]
                latest_student.append(i.id)

            students = []
            if current_student_rec:
                for rec in current_student_sibling_records:
                    map_record = self.env["xe.student"].sudo().browse(rec.id)
                    for i in student_records:
                        if rec.id != i.id:
                            students.append(i.id)

                    if students:
                        rec.is_siblings = True
                        lists = current_student_rec + rec.student_ids
                        if map_record.student_ids:
                            students = [i.id for i in lists]
                        # Update Siblings to another student Siblings tabs
                        map_record.student_ids = [(6, 0, students)]

                        vals = []
                        # Fetch the current student siblings list and updated to another students siblings
                        for j in map_record.student_ids:
                            if j.id != current_student_rec.id:
                                vals = [x.id for x in j.student_ids]
                                vals.append(current_student_rec.id)
                            if vals:
                                j.student_ids = [(6, 0, vals)]

                    # Selected Students Sibling Details add to the Current student siblings tabs.
                    siblings = []
                    current_student_rec = self.student_id
                    for i in self.sibling_ids:
                        siblings.append(i.id)
                        for j in i.student_ids:
                            siblings.append(j.id)
                            for k in j.student_ids:
                                siblings.append(k.id)

                    students = []
                siblings = list(set(siblings))
                siblings.remove(current_student_rec.id)
                current_student_rec.student_ids = [(6, 0, siblings)]

                # fetching Parent Details update to current records
                parent_ids = []
                for i in current_student_rec.parent_ids:
                    parent_ids.append(i.id)
                for j in map_record.parent_ids:
                    parent_ids.append(j.id)
                    for x in j.student_ids.parent_ids:
                        parent_ids.append(x.id)
                current_student_rec.write(
                    {"parent_ids": [(6, 0, list(set(parent_ids)))]}
                )

                for records in map_record.student_ids:
                    sib_p_ids = [k.id for k in records.student_ids.parent_ids]
                    for p in current_student_rec.parent_ids:
                        sib_p_ids.append(p.id)
                    if sib_p_ids:
                        records.parent_ids = [(6, 0, sib_p_ids)]
                rec.parent_ids = [(6, 0, sib_p_ids)]
            else:
                current_student_rec.student_ids = [(6, 0, [])]
