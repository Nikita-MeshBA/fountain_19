from odoo import api, fields, models


class ReportStudentInformation(models.AbstractModel):
    _name = "report.xe_transportation_management.report_transports"
    _description = "Transportation Details Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        route_ids = data["form"]["route_ids"]
        route_line_data = self.env["xe.route"].browse(route_ids)
        docs = []
        if route_line_data:
            docids = route_line_data.ids
            docs = route_line_data

        return {
            "doc_ids": docids,
            "doc_model": "xe.route",
            "data": data["form"],
            "docs": docs,
        }
