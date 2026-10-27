from odoo import models
from datetime import datetime, timedelta
import base64
import io
from PIL import Image


class TransportXlsx(models.AbstractModel):
    _name = "report.xe_transportation_management.transport_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Transportation xlsx"

    def generate_xlsx_report(self, workbook, data, payslip):
        header_format = workbook.add_format(
            {"font_size": 10, "align": "center", "bold": True, "font_name": "Arial"}
        )
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("transport_report")
        company_id = self.env.company
        product_image = company_id.logo
        if product_image:
            imgdata = base64.b64decode(product_image)
            image = io.BytesIO(imgdata)
            im = Image.open(io.BytesIO(imgdata))
            width, height = im.size
            if width > 500 or height > 500:
                x_scale = 0.10
                y_scale = 0.10
            else:
                x_scale = 0.20
                y_scale = 0.20
            sheet.insert_image(
                "A1",
                "myimage.png",
                {"image_data": image, "x_scale": x_scale, "y_scale": y_scale},
            )
        company_address1 = ""
        company_address2 = ""
        company_address3 = ""
        company_address4 = ""
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
        sheet.write(0, 1, company_id.name, format1)
        if company_address1:
            row1 += 1
            sheet.write(row1, 1, company_address1, format1)
        if company_address2:
            row1 += 1
            sheet.write(row1, 1, company_address2, format1)
        if company_address3:
            row1 += 1
            sheet.write(row1, 1, company_address3, format1)
        if company_address4:
            row1 += 1
            sheet.write(row1, 1, company_address4, format1)
        if company_id.website:
            row1 += 1
            sheet.write(row1, 1, company_id.website, format1)
        row = row1 + 2
        sheet.merge_range(row, 0, row, 3, "Transportation Details", header_format)
        routes = self.env["xe.route"].browse(data["form"]["route_ids"])
        row = row + 2
        sheet.write(row, 0, "Route", format1)
        sheet.write(row, 1, "Stop", format1)
        sheet.write(row, 2, "Admission Number", format1)
        sheet.write(row, 3, "Passenger", format1)
        sheet.set_column(0, 4, 27)
        row += 1
        for route in routes:
            for stop in route.stop_ids:
                for partner in stop.partner_ids:
                    sheet.write(row, 0, route.name, format2)
                    sheet.write(row, 1, stop.name, format2)
                    sheet.write(row, 2, partner.roll_number, format2)
                    sheet.write(row, 3, partner.name, format2)
                    row += 1
