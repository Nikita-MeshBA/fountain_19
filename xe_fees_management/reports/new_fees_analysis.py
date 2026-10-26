# -*- coding: utf-8 -*-
###############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import models, api


class ReportFeesAnalysis(models.AbstractModel):
    _name = "report.xe_fees_management.report_new_fees_analysis"
    _description = "Admission Management New Fees Analysis Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        line_data = {}
        header_rows = ["roll_number", "student"]
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        date_domain = [
            ("create_date", ">=", date_from),
            ("create_date", "<=", date_to),
        ]

        student_ids = self.env["xe.student"].browse(docids)
        if data.get("fees_filter") == "student":
            student_ids = self.env["xe.student"].browse([data["student"]])
            domain = [
                ("partner_id", "=", student_ids.partner_id.id),
                ("state", "in", ["posted"]),
                ("move_type", "=", "out_invoice"),
            ]
            if date_from and date_to:
                domain += date_domain
            invoices = self.env["account.move"].search(domain)

        elif data.get("fees_filter") == "classroom":
            domain = [
                ("state", "in", ["posted"]),
                ("class_room_id", "=", data["classroom"]),
                ("move_type", "=", "out_invoice"),
            ]
            if date_from and date_to:
                domain += date_domain
            invoices = self.env["account.move"].search(domain)

        elif data.get("fees_filter") == "course" and data["course"]:
            domain = [
                ("state", "in", ["posted"]),
                ("move_type", "=", "out_invoice"),
                ("course_id", "in", data["course"]),
            ]
            if date_from and date_to:
                domain += date_domain
            invoices = self.env["account.move"].search(domain)

        students = []
        for i in invoices.mapped("partner_id"):
            student_rec = (
                self.env["xe.student"]
                .sudo()
                .search([("partner_id", "=", i.id)], limit=1)
            )
            if not student_rec:
                student_rec = (
                    self.env["xe.student"]
                    .sudo()
                    .create(
                        {
                            "name": i.name,
                            "partner_id": i.id,
                            "gender": "male",
                            "course_id": self.env["xe.course"]
                            .sudo()
                            .search([], limit=1)
                            .id,
                        }
                    )
                )
            students.append(student_rec)

        line_datas = []
        for inv in invoices:
            product_data = {}
            total_amount = 0
            paid_amount = 0
            discount_fixed = 0
            total_discount = 0
            product_data["student"] = inv.partner_id.name
            product_data["roll_number"] = (
                self.env["xe.student"]
                .sudo()
                .search([("name", "=", inv.partner_id.name)], limit=1)
                .roll_number
            )
            for invoice in inv:
                for line in invoice.invoice_line_ids:
                    if line.product_id.name not in header_rows:
                        header_rows.append(line.product_id.name)
                    product_data[line.product_id.name] = line.price_subtotal
                    discount_fixed = discount_fixed + line.discount_fixed

                total_amount += invoice.amount_total
                total_discount += discount_fixed
                if invoice.state != "draft":
                    paid_amount += invoice.amount_total - invoice.amount_residual
            if total_amount > 0:
                product_data["total_amount"] = total_amount
                product_data["total_discount"] = discount_fixed
            else:
                product_data["total_amount"] = 0.0
                product_data["total_discount"] = 0.0
            if paid_amount > 0:
                product_data["paid_amount"] = paid_amount
            else:
                product_data["paid_amount"] = 0.0
            balance_amount = total_amount - paid_amount
            if balance_amount > 0:
                product_data["balance_amount"] = balance_amount
            else:
                product_data["balance_amount"] = 0.0
            product_data["partner_balance"] = invoice._partner_balance_new(
                inv.partner_id.id
            )
            # Credit Note amount calculation
            out_invoice_rec = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("state", "in", ["posted"]),
                        ("move_type", "=", "out_refund"),
                        ("partner_id", "=", inv.partner_id.id),
                    ]
                )
            )
            move_list_id = out_invoice_rec.mapped("id")
            if out_invoice_rec:
                move_line_ids = (
                    self.env["account.move.line"]
                    .sudo()
                    .search(
                        [
                            ("partner_id", "=", inv.partner_id.id),
                            ("move_id", "in", move_list_id),
                            ("name", "=", False),
                        ]
                    )
                )
                credit_amount = sum(move_line_ids.mapped("credit"))
                product_data["credit_note"] = credit_amount
            else:
                product_data["credit_note"] = 0.0

            if total_amount > 0:
                line_data[inv.partner_id.name] = product_data

            line_datas.append(product_data)

        header_rows.append("total_amount")
        header_rows.append("total_discount")
        header_rows.append("paid_amount")
        header_rows.append("balance_amount")
        header_rows.append("credit_note")
        header_rows.append("partner_balance")

        from operator import itemgetter

        line_datas = sorted(line_datas, key=lambda x: str(itemgetter("roll_number")))

        def group_sum(key, list_of_dicts):
            d = {}
            lst_items = ["roll_number", "credit_note", "partner_balance"]
            for dct in list_of_dicts:
                if dct[key] not in d:
                    d[dct[key]] = {}
                for k, v in dct.items():
                    if k != key:
                        if k not in d[dct[key]]:
                            d[dct[key]][k] = v
                        else:
                            if k not in lst_items:
                                d[dct[key]][k] += v
            final_list = []
            for k, v in d.items():
                temp_d = {key: k}
                for k2, v2 in v.items():
                    temp_d[k2] = v2
                final_list.append(temp_d)
            return final_list

        grouped_data = group_sum("student", line_datas)

        docargs = {
            "doc_ids": self.ids,
            "doc_model": "xe.student",
            "docs": student_ids,
            "header_rows": header_rows,
            "line_data": grouped_data,
            "data": data,
        }
        return docargs
