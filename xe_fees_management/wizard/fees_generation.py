from odoo import fields, models


class FeesGeneration(models.TransientModel):
    _name = "xe.fees.generation"
    _description = "Fees Generation"

    def default_academic_year(self):
        config_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .search(
                [("key", "=", "xenesis_school_base.current_academic_year_id")], limit=1
            )
        )
        if config_param:
            academic_id = config_param.value
            academic_rec = (
                self.env["xe.academic.year"].sudo().search([("id", "=", academic_id)])
            )
            return academic_rec and academic_rec.id or False

    current_academic_year_id = fields.Many2one(
        "xe.academic.year", default=default_academic_year
    )
    fee_structure_ids = fields.Many2many(
        "xe.fees.structure",
        domain="[('academic_year_id', '=', current_academic_year_id)]",
    )
    term_id = fields.Many2one(
        "xe.academic.terms",
        domain="[('academic_year_id', '=', current_academic_year_id)]",
        string="Academic Term",
    )

    def action_generation(self):
        if self.fee_structure_ids:
            student_rec = []
            fee_struc_ids = []
            course_ids = []
            classroom_ids = []
            term = self.term_id.id
            course = self.fee_structure_ids.course_id.ids
            classroom = self.fee_structure_ids.classroom_id.ids
            student_domain = [
                ("current_academic_year_id", "=", self.current_academic_year_id.id)
            ]
            if course:
                student_domain.append(("course_id", "in", course))
            if classroom:
                student_domain.append(("classroom_id", "in", classroom))
            for fees in self.fee_structure_ids:
                # Academic Logic
                # if fees.fee_structu_type == "academic" and not fees.is_include_transport_fees and not fees.is_include_optional_fees and not fees.is_include_activity_fees:
                if fees.fee_structu_type == "academic":
                    fees.with_context(term_id=term).generate()

                    student_rec = self.env["xe.student"].search(student_domain)
                    fee_struc_ids.append(fees.id)
                    for i in fees.course_id.ids:
                        course_ids.append(i)
                    for j in fees.classroom_id.ids:
                        classroom_ids.append(j)

                # Transport Logic
                # elif fees.fee_structu_type == "transport":
                # elif fees.fee_structu_type == "academic" and fees.fee_details_ids.filtered(lambda r : r.fee_type_id == "transport"):
                # elif fees.fee_structu_type == "academic" and fees.is_include_transport_fees:
                # single_inv = self.env['ir.config_parameter'].sudo().get_param('xe_fees_management.is_transport')
                if (
                    fees.fee_structu_type == "academic"
                    and fees.is_include_transport_fees
                ):
                    single_inv = (
                        self.env["ir.config_parameter"]
                        .sudo()
                        .search(
                            [("key", "=", "xe_fees_management.is_transport")], limit=1
                        )
                    )
                    if single_inv:
                        transport_domain = student_domain
                        transport_domain.append(("is_transport", "=", True))
                        student_rec = self.env["xe.student"].search(transport_domain)
                        fees.with_context(
                            student_rec=student_rec,
                            term_id=term,
                        ).generate_transport()
                    else:
                        fees.with_context(term_id=term).generate_transport()

                # Optional Fee
                # elif fees.fee_structu_type == "optional":
                # elif fees.fee_structu_type == "academic" and fees.is_include_optional_fees:
                # single_invop = self.env['ir.config_parameter'].sudo().get_param('xe_fees_management.is_optional')
                if (
                    fees.fee_structu_type == "academic"
                    and fees.is_include_optional_fees
                ):
                    single_invop = (
                        self.env["ir.config_parameter"]
                        .sudo()
                        .search(
                            [("key", "=", "xe_fees_management.is_optional")], limit=1
                        )
                    )
                    if single_invop:
                        optional_domain = student_domain
                        optional_domain.append(("is_optional", "=", True))
                        student_rec = self.env["xe.student"].search(optional_domain)
                        fees.with_context(
                            student_rec=student_rec, term_id=term
                        ).generate_optional()
                    else:
                        fees.with_context(term_id=term).generate_optional()
                # Activity Fee
                # elif fees.fee_structu_type == "activity":
                # elif fees.fee_structu_type == "academic" and fees.is_include_activity_fees:
                # single_inv_act = self.env['ir.config_parameter'].sudo().get_param('xe_fees_management.is_activity')
                if (
                    fees.fee_structu_type == "academic"
                    and fees.is_include_activity_fees
                ):
                    single_inv_act = (
                        self.env["ir.config_parameter"]
                        .sudo()
                        .search(
                            [("key", "=", "xe_fees_management.is_activity")], limit=1
                        )
                    )
                    if single_inv_act:
                        activity_domain = student_domain
                        activity_domain.append(("is_activity", "=", True))
                        student_rec = self.env["xe.student"].search(activity_domain)
                        fees.with_context(
                            student_rec=student_rec, term_id=term
                        ).generate_activity()
                    else:
                        fees.with_context(
                            fee_struc_ids=fee_struc_ids, term_id=term
                        ).generate_activity()
                # Boarding Fee
                if fees.fee_structu_type == "boarding":
                    single_inv_act = (
                        self.env["ir.config_parameter"]
                        .sudo()
                        .search(
                            [("key", "=", "xe_fees_management.is_boarding")], limit=1
                        )
                    )
                    if single_inv_act:
                        boarding_domain = student_domain
                        boarding_domain.append(("is_boarding_invoice", "=", False))
                        student_rec = self.env["xe.student"].search(boarding_domain)
                        fees.with_context(
                            student_rec=student_rec, term_id=term
                        ).generate_boarding()
                    else:
                        fees.with_context(
                            fee_struc_ids=fees, term_id=term
                        ).generate_boarding()
            # Update fee structure lines
            fee_line_ids = self.fee_structure_ids.fee_details_ids
            for line in fee_line_ids:
                if line.term_id.id == self.term_id.id:
                    line.write({"parent_state": "invoice"})

            # Update Customer name to Invoice (Optional)
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search([("partner_id", "=", False), ("is_optional", "=", True)])
            )
            for inv in account_move_rec:
                student_rec = self._get_student(inv.roll_number)
                if student_rec:
                    inv.partner_id = student_rec.partner_id.id

            # Update Customer name to Invoice (Transport)
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search([("partner_id", "=", False), ("is_transport_fees", "=", True)])
            )
            for inv in account_move_rec:
                student_rec = self._get_student(inv.roll_number)
                if student_rec:
                    inv.partner_id = student_rec.partner_id.id

            # Update Customer name to Invoice (Academic)
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search([("partner_id", "=", False), ("is_academic", "=", True)])
            )
            for inv in account_move_rec:
                student_rec = self._get_student(inv.roll_number)
                if student_rec:
                    inv.partner_id = student_rec.partner_id.id

            # Update Customer name to Invoice (activity)
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search([("partner_id", "=", False), ("is_activity", "=", True)])
            )
            for inv in account_move_rec:
                student_rec = self._get_student(inv.roll_number)
                if student_rec:
                    inv.partner_id = student_rec.partner_id.id

            # Update Customer name to Invoice (boarding)
            account_move_rec = (
                self.env["account.move"]
                .sudo()
                .search([("partner_id", "=", False), ("is_boarding", "=", True)])
            )
            for inv in account_move_rec:
                student_rec = self._get_student(inv.roll_number)
                if student_rec:
                    inv.partner_id = student_rec.partner_id.id

    def _get_student(self, roll_number):
        return (
            self.env["xe.student"]
            .sudo()
            .search([("roll_number", "=", roll_number)], limit=1)
        )
