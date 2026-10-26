from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, _


class StudentProfile(models.Model):
    _inherit = "xe.student"
    _rec_name = "name"

    application_id = fields.Many2one("xe.application", string="Source Document")
    transportation_term_id = fields.Many2one("xe.fees.term.line", "Transportation Fees")
    fees_detail_line_ids = fields.One2many(
        "xe.student.fees.details", "student_id", "Fees Collection Details"
    )
    enquiry_id = fields.Many2one("xe.admission.enquiry", string="Enquiry")
    parent_id = fields.Many2one("xe.admission.enquiry")

    @api.model
    def generate_fees_lines1(self):
        students_with_no_line = self.env["xe.student"].search([])
        for stud in students_with_no_line:
            final_fee_vals = []
            course_line = self.env["xe.student.course"].search(
                [("student_id", "=", stud.id)]
            )
            val = []
            if (
                course_line
                and course_line.course_id
                and course_line.course_id.fees_term_id
                and course_line.course_id.fees_term_id.fees_line
            ):
                for line in course_line.course_id.fees_term_id.fees_line:
                    date_feesterm_tuple = (line.id, line.start)
                    val.append(date_feesterm_tuple)
            if stud.transportation_term_id:
                date_feesterm_tuple = (
                    stud.transportation_term_id.id,
                    stud.transportation_term_id.start,
                )
                val.append(date_feesterm_tuple)
            grouped_dict = self.get_grouped(val)
            for rec in grouped_dict:
                fee_termline_ids = rec["line_ids"]
                fee_termline_obj = self.env["xe.fees.term.line"].browse(
                    fee_termline_ids
                )
                fee_term_ids_array = []
                fee_term_pdt_ids_array = []
                fee_line_ids = []
                date = rec["date"]
                amount = 0
                for li in fee_termline_obj:
                    amount = amount + li.value
                    fee_term_ids_array.append(int(li.id))
                    fee_term_pdt_ids_array.append(li.product_id and li.product_id.id)
                    fee_vals = {"fee_term_line_id": li.id}
                    fee_line_ids.append((0, 0, fee_vals))
                dict_val = {
                    "state": "draft",
                    "amount": amount,
                    "fees_term_line_ids": [(6, 0, fee_term_ids_array)],
                    "product_ids": [(6, 0, fee_term_pdt_ids_array)],
                    "date": date,
                    "fee_sub_line_ids": fee_line_ids,
                }
                final_fee_vals.append([0, False, dict_val])
            stud.write({"fees_detail_line_ids": final_fee_vals})
