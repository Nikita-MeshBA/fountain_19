# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116
import binascii
import tempfile

import xlrd
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, _


class CBCWorkExcelExp(models.AbstractModel):
    _name = "report.xe_lesson_planner.cbc_work_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "CBC Work Report"

    def generate_xlsx_report(self, workbook, data, attendance):
        heading = workbook.add_format(
            {"font_size": 13, "align": "center", "bold": True, "font_name": "Arial"}
        )
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("cbc_work_report")
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 13)
        sheet.set_column(2, 2, 13)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 42)
        sheet.set_column(5, 5, 46)
        sheet.set_column(6, 6, 40)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 42)
        sheet.set_column(9, 9, 35)
        row = 0
        sheet.write(row, 0, "WEEK", heading)
        sheet.write(row, 1, "LESSON", heading)
        sheet.write(row, 2, "STRAND", heading)
        sheet.write(row, 3, "SUB STRAND", heading)
        sheet.write(row, 4, "SPECIFIC LEARNING OUTCOMES", heading)
        sheet.write(row, 5, "SUGGESTED LEARNING EXPERIENCES", heading)
        sheet.write(row, 6, "KEY INQUIRY QUESTIONS", heading)
        sheet.write(row, 7, "LEARNING RESOURCES", heading)
        sheet.write(row, 8, "ASSESSMENT TECHNIQUES", heading)
        sheet.write(row, 9, "REFLECTION", heading)
        row = 1
        rec_id = self.env["cbc.scheme.of.work"].search([('id','=',data.get("context").get("active_id"))])
        if rec_id.cbc_scheme_of_work_ids:  
            for work_id in rec_id.cbc_scheme_of_work_ids:
                sheet.write(row, 0, str(work_id.week or ''), format1)
                sheet.write(row, 1, str(work_id.lesson or ''), format1)
                sheet.write(row, 2, str(work_id.topic or ''), format1)
                sheet.write(row, 3, str(work_id.sub_topic or ''), format1)
                sheet.write(row, 4, str(work_id.objectives or ''), format1)
                sheet.write(row, 5, str(work_id.learning_activities or ''), format1)
                sheet.write(row, 6, str(work_id.key_inquiry_questions or ''), format1)
                sheet.write(row, 7, str(work_id.learning_resources or ''), format1)
                sheet.write(row, 8, str(work_id.assessment_methods or ''), format1)
                sheet.write(row, 9, str(work_id.remarks or ''), format1)
                row += 1


class ImportCBCWorkLine(models.TransientModel):
    _name = "import.cbc.work.line"

    file = fields.Binary()
    filename = fields.Char()

    def action_upload(self):
        active_id = self.env.context.get("active_id")
        # rec_id = self.env["cbc.scheme.of.work"].browse(active_id)
        # print('\n\n\t\t--------------- this is rec_id : ', rec_id)

        if not self.file:
            raise UserError(_("Please upload xls/xlsx file first !!"))

        try:
            tempfile_xlsx = tempfile.NamedTemporaryFile(delete=True)
            tempfile_xlsx.write(binascii.a2b_base64(self.file))
            tempfile_xlsx.seek(0)
            sheet = xlrd.open_workbook(
                file_contents=tempfile_xlsx.read()
            ).sheet_by_index(0)
            write_data = []
            for row_index in range(1, sheet.nrows):
                data = sheet.row_values(row_index)
                data_dict = {
                    "week": data[0],
                    "lesson": data[1],
                    "topic": data[2],
                    "sub_topic": data[3],
                    "objectives": data[4],
                    "learning_activities": data[5],
                    "key_inquiry_questions": data[6],
                    "learning_resources": data[7],
                    "assessment_methods": data[8],
                    "remarks": data[9],
                    "cbc_scheme_of_work_id": active_id,
                    }
                write_data.append(data_dict)
            self.env["cbc.scheme.of.work.line"].create(write_data)


            #     if not data[0]:
            #         raise ValidationError(
            #             _("Subject empty in row no." + str(row_index + 1) + ".")
            #         )
            #     if not data[1]:
            #         raise ValidationError(
            #             _("Code empty in row no." + str(row_index + 1) + ".")
            #         )
            #     if not data[2]:
            #         raise ValidationError(
            #             _("Description empty in row no." + str(row_index + 1) + ".")
            #         )

            #     subject_id = self.env["xe.subject"].search(
            #         [
            #             ("name", "=", data[0]),
            #             ("course_ids", "in", [session_id.course_id.id]),
            #         ],
            #         limit=1,
            #     )
            #     if not subject_id:
            #         raise ValidationError(
            #             _(
            #                 f"Subject name in row no.%s not match in"
            #                 f" Subjects configuration. {str(row_index + 1)}"
            #             )
            #         )

            #     subject_session_exists = session_id.exam_ids.filtered(
            #         lambda row_index: row_index.subject_id == subject_id
            #     )
            #     if not subject_session_exists:
            #         raise ValidationError(
            #             _(
            #                 f"Subject in row no.%s not in exam session.{str(row_index + 1)}"
            #             )
            #         )

            #     rubrics_code_id = self.env["xe.rubrics.code"].search(
            #         [("code", "=", data[1])], limit=1
            #     )
            #     if not rubrics_code_id:
            #         raise ValidationError(
            #             _(
            #                 f"Code in row no.%s not match in "
            #                 f"Rubrics code configuration. {str(row_index + 1)}"
            #             )
            #         )
            #     rubrics_name_id = self.env["xe.rubrics.code"].search(
            #         [("name", "=", data[2])], limit=1
            #     )
            #     if not rubrics_name_id:
            #         raise ValidationError(
            #             _(
            #                 f"Description in row no.%s not match in "
            #                 f"Rubrics code configuration. {str(row_index + 1)}"
            #             )
            #         )

            # if session_id.rubrics_ids:
            #     session_id.rubrics_ids = False

            # for i in range(1, sheet.nrows):
            #     idata = sheet.row_values(i)
            #     new_subject_id = self.env["xe.subject"].search(
            #         [
            #             ("name", "=", idata[0]),
            #             ("course_ids", "in", [session_id.course_id.id]),
            #         ],
            #         limit=1,
            #     )
            #     rubrics_id = self.env["xe.rubrics.code"].search(
            #         [("code", "=", idata[1]), ("name", "=", idata[2])], limit=1
            #     )
            #     if new_subject_id and rubrics_id:
            #         vals = {
            #             "exam_session_id": session_id.id,
            #             "subject_id": new_subject_id.id,
            #             "new_code_id": rubrics_id.id,
            #             "name": rubrics_id.name,
            #             "min_per": int(idata[3]),
            #             "max_per": int(idata[4]),
            #         }
            #         session_id.rubrics_ids = [(0, 0, vals)]
        except Exception as error:
            raise ValidationError(error)
