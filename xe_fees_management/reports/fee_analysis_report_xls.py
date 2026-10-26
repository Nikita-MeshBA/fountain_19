import base64
import io
import string

from odoo import models

total_column = {}
sub_total_column = {}


class FeeAnalysisXlsx(models.AbstractModel):
    _name = "report.xe_fees_management.report_fees_analysis_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Fee Analysis xlsx"

    def generate_xlsx_report(self, workbook, data, wizard):
        header_format = workbook.add_format(
            {"font_size": 15, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        header_format.set_center_across()
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 15, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("fee_analysis_report")
        data_format1 = workbook.add_format(
            {"font_size": 10, "align": "left", "font_name": "Arial"}
        )
        data_format2 = workbook.add_format(
            {"font_size": 10, "align": "left", "font_name": "Arial"}
        )
        date_start = data["date_from"]
        date_end = data["date_to"]

        company_id = self.env["res.company"].browse(int(data["company"]))
        if company_id:
            company_address1 = company_address2 = company_address3 = (
                company_address4
            ) = ""
            if company_id.street:
                company_address1 = company_id.street + ","
            if company_id.street2:
                company_address1 += company_id.street2
            if company_id.city:
                company_address2 = company_id.city + ","
            if company_id.state_id.name:
                company_address2 += company_id.state_id.name
            if company_id.country_id:
                company_address3 = company_id.country_id.name
            if company_id.email:
                company_address4 = company_id.email + ","
            if company_id.phone:
                company_address4 += company_id.phone
            row1 = 0
            sheet.write(0, 3, company_id.name, format2)
            if company_address1:
                sheet.write(row1, 6, company_address1, format1)
            if company_address2:
                row1 += 1
                sheet.write(row1, 6, company_address2, format1)
            if company_address3:
                row1 += 1
                sheet.write(row1, 6, company_address3, format1)
            if company_address4:
                row1 += 1
                sheet.write(row1, 6, company_address4, format1)
            if company_id.website:
                row1 += 1
                sheet.write(row1, 6, company_id.website, format1)

            if company_id.logo:
                product_image = company_id.logo
                imgdata = base64.b64decode(product_image)
                image = io.BytesIO(imgdata)

                image_width = 100.0
                image_height = 300.0
                cell_width = 90
                cell_height = 200.0
                x_scale = cell_width / image_width
                y_scale = cell_height / image_height

                sheet.merge_range("A1:C5", "")
                sheet.insert_image(
                    "A1:C5",
                    "myimage.png",
                    {"image_data": image, "x_scale": x_scale, "y_scale": y_scale},
                )
                row1 = 4
            row = row1 + 2
        else:
            row = 2
        sheet.merge_range(row, 0, row, 8, str(data["report_name"]), header_format)
        row += 1
        sheet.write(row, 0, "Start Date", format1)
        sheet.write(row, 1, date_start, format1)
        sheet.write(row, 3, "End Date", format1)
        sheet.write(row, 4, date_end, format1)

        date_domain = [
            ("create_date", ">=", date_start),
            ("create_date", "<=", date_end),
        ]

        if data.get("fees_filter") == "student":
            student_id = self.env["xe.student"].browse([data["student"]])
            sheet.write(row, 6, "Student", format1)
            sheet.write(row, 7, student_id.name, format1)

            domain = [
                ("partner_id", "=", student_id.partner_id.id),
                ("state", "in", ["posted"]),
                ("move_type", "=", "out_invoice"),
            ]
            if date_start and date_end:
                domain += date_domain
            invoices = self.env["account.move"].search(domain)

        elif data.get("fees_filter") == "classroom":
            sheet.write(row, 6, "Class Room", format1)
            sheet.write(row, 7, data["classroom_name"], format1)

            domain = [
                ("state", "in", ["posted"]),
                ("class_room_id", "=", data["classroom"]),
                ("move_type", "=", "out_invoice"),
            ]
            if date_start and date_end:
                domain += date_domain
            invoices = self.env["account.move"].search(domain)

        elif data.get("fees_filter") == "course" and data["course"]:
            sheet.write(row, 6, "Class", format1)
            sheet.write(row, 7, data["course_name"], format1)

            domain = [
                ("state", "in", ["posted"]),
                ("move_type", "=", "out_invoice"),
                ("course_id", "in", data["course"]),
            ]
            if date_start and date_end:
                domain += date_domain
            invoices = self.env["account.move"].search(domain)

        students = []
        for i in invoices.mapped("partner_id"):
            student_rec = (
                self.env["xe.student"]
                .sudo()
                .with_context(active_test=False)
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

        row += 2
        header_rows = ["admission_number", "class", "classroom", "student"]
        line_datas = []
        data_dict = {}
        for inv in invoices:
            product_data = {}
            total_amount = 0
            paid_amount = 0
            discount_fixed = 0
            total_discount = 0
            product_data["student"] = inv.partner_id.name
            student = (
                self.env["xe.student"]
                .sudo()
                .search([("name", "=", inv.partner_id.name)], limit=1)
            )
            product_data["admission_number"] = student.roll_number or ""
            product_data["class"] = student.course_id.name or ""
            product_data["classroom"] = (
                student.classroom_id.name if student.classroom_id else ""
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
                product_data["total_discount"] = total_discount
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
                product_data["credit_note_amount"] = credit_amount
            else:
                product_data["credit_note_amount"] = 0.0

            if total_amount > 0:
                data_dict[inv.partner_id.name] = product_data

            line_datas.append(product_data)
        header_rows.append("total_amount")
        header_rows.append("total_discount")
        header_rows.append("paid_amount")
        header_rows.append("credit_note_amount")
        header_rows.append("partner_balance")

        new_header_rows = []
        for i in range(0, len(header_rows)):
            list_vals = ""
            if header_rows[i] == "partner_balance":
                list_vals = "Balance Amount"
            elif header_rows[i]:
                header_lead_space_remove = header_rows[i].strip()
                header_remove_underscore = header_lead_space_remove.replace("_", " ")
                list_vals = string.capwords(header_remove_underscore)
            new_header_rows.append(list_vals)
        col = 0
        for h in range(0, len(header_rows)):
            sheet.write(row, col, new_header_rows[h], format1)
            col += 1
        row = row + 1

        from operator import itemgetter

        line_datas = sorted(line_datas, key=lambda x: str(itemgetter("roll_number")))

        def group_sum(key, list_of_dicts):
            d = {}
            lst_items = [
                "admission_number",
                "class",
                "classroom",
                "credit_note_amount",
                "partner_balance",
            ]
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

        line_datas = group_sum("student", line_datas)
        col = 0
        line_datas = sorted(line_datas, key=lambda x: x.get("class"))
        for data in line_datas:
            if (row % 2) == 0:
                cell_format = data_format1
            else:
                cell_format = data_format2
            for h in range(0, len(header_rows)):
                if "student" in data and header_rows[h] == "student":
                    sheet.write(row, col, data.get("student"), cell_format)
                    sheet.set_column(row, col, 14)
                elif (
                    "admission_number" in data and header_rows[h] == "admission_number"
                ):
                    sheet.write(row, col, data.get("admission_number"), cell_format)
                    sheet.set_column(row, col, 14)
                elif "class" in data and header_rows[h] == "class":
                    sheet.write(row, col, data.get("class"), cell_format)
                    sheet.set_column(row, col, 20)
                elif "classroom" in data and header_rows[h] == "classroom":
                    sheet.write(row, col, data.get("classroom"), cell_format)
                    sheet.set_column(row, col, 20)
                elif header_rows[h] in data:
                    sheet.write(row, col, data.get(header_rows[h]), cell_format)
                elif "total_amount" in data and header_rows[h] == "total_amount":
                    sheet.write(row, col, data.get("total_amount"), cell_format)
                elif "total_discount" in data and header_rows[h] == "total_discount":
                    sheet.write(row, col, data.get("total_discount"), cell_format)
                elif "paid_amount" in data and header_rows[h] == "paid_amount":
                    sheet.write(row, col, data.get("paid_amount"), cell_format)
                elif (
                    "credit_note_amount" in data
                    and header_rows[h] == "credit_note_amount"
                ):
                    sheet.write(row, col, data.get("credit_note_amount"), cell_format)
                elif "partner_balance" in data and header_rows[h] == "partner_balance":
                    sheet.write(
                        row, col, float(data.get("partner_balance")), cell_format
                    )
                else:
                    sheet.write(row, col, 0.0, cell_format)
                col += 1
            col = 0
            row = row + 1
