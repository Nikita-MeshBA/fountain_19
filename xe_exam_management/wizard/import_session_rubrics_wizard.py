import binascii
import tempfile

import xlrd
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, _


class ImportSessionRubrics(models.TransientModel):
    _name = "import.session.rubrics"

    file = fields.Binary()
    filename = fields.Char()

    def action_upload(self):
        active_id = self.env.context.get("active_id")
        session_id = self.env["xe.exam.session"].browse(active_id)

        if not self.file:
            raise UserError(_("Please upload xls/xlsx file first !!"))

        if not session_id.exam_ids:
            raise UserError(_("Session have no exams."))

        try:
            tempfile_xlsx = tempfile.NamedTemporaryFile(delete=True)
            tempfile_xlsx.write(binascii.a2b_base64(self.file))
            tempfile_xlsx.seek(0)
            sheet = xlrd.open_workbook(
                file_contents=tempfile_xlsx.read()
            ).sheet_by_index(0)

            for row_index in range(1, sheet.nrows):
                data = sheet.row_values(row_index)
                if not data[0]:
                    raise ValidationError(
                        _("Subject empty in row no." + str(row_index + 1) + ".")
                    )
                if not data[1]:
                    raise ValidationError(
                        _("Code empty in row no." + str(row_index + 1) + ".")
                    )
                if not data[2]:
                    raise ValidationError(
                        _("Description empty in row no." + str(row_index + 1) + ".")
                    )

                subject_id = self.env["xe.subject"].search(
                    [
                        ("name", "=", data[0]),
                        ("course_ids", "in", [session_id.course_id.id]),
                    ],
                    limit=1,
                )
                if not subject_id:
                    raise ValidationError(
                        _(
                            f"Subject name in row no.%s not match in"
                            f" Subjects configuration. {str(row_index + 1)}"
                        )
                    )

                subject_session_exists = session_id.exam_ids.filtered(
                    lambda row_index: row_index.subject_id == subject_id
                )
                if not subject_session_exists:
                    raise ValidationError(
                        _(
                            f"Subject in row no.%s not in exam session.{str(row_index + 1)}"
                        )
                    )

                rubrics_code_id = self.env["xe.rubrics.code"].search(
                    [("code", "=", data[1])], limit=1
                )
                if not rubrics_code_id:
                    raise ValidationError(
                        _(
                            f"Code in row no.%s not match in "
                            f"Rubrics code configuration. {str(row_index + 1)}"
                        )
                    )
                rubrics_name_id = self.env["xe.rubrics.code"].search(
                    [("name", "=", data[2])], limit=1
                )
                if not rubrics_name_id:
                    raise ValidationError(
                        _(
                            f"Description in row no.%s not match in "
                            f"Rubrics code configuration. {str(row_index + 1)}"
                        )
                    )

            if session_id.rubrics_ids:
                session_id.rubrics_ids = False

            for i in range(1, sheet.nrows):
                idata = sheet.row_values(i)
                new_subject_id = self.env["xe.subject"].search(
                    [
                        ("name", "=", idata[0]),
                        ("course_ids", "in", [session_id.course_id.id]),
                    ],
                    limit=1,
                )
                rubrics_id = self.env["xe.rubrics.code"].search(
                    [("code", "=", idata[1]), ("name", "=", idata[2])], limit=1
                )
                if new_subject_id and rubrics_id:
                    vals = {
                        "exam_session_id": session_id.id,
                        "subject_id": new_subject_id.id,
                        "new_code_id": rubrics_id.id,
                        "name": rubrics_id.name,
                        "min_per": int(idata[3]),
                        "max_per": int(idata[4]),
                    }
                    session_id.rubrics_ids = [(0, 0, vals)]
        except Exception as error:
            raise ValidationError(error)
