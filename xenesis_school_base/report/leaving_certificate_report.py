from datetime import date

from odoo import models, api


class LeavingCertificateReport(models.AbstractModel):
    _name = "report.xenesis_school_base.report_leaving_certificate"
    _description = "Report Leaving Certificates"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["xe.student"].browse(data.get("docids"))

        attribute_lines_ids = self.env["xe.certificate.atts.lines"].browse(
            data.get("attribute_lines_ids")
        )
        current_date = date.today().strftime("%d-%m-%Y")
        return {
            "doc_ids": docids,
            "doc_model": "xe.student",
            "docs": docs,
            "data": data,
            "current_date": current_date,
            "attribute_lines_ids": attribute_lines_ids,
        }
