from odoo import models, api


class ClearanceReport(models.AbstractModel):
    _name = "report.xenesis_school_base.report_clearance_form"
    _description = "Report Clearance Form"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["xe.student"].browse(data.get("docids"))
        parent = self.env["xe.parent"].browse(data.get("parent_id"))
        attribute_lines_ids = self.env["xe.clearance.attribute.line"].browse(
            data.get("attribute_lines_ids")
        )
        part_a_lines = []
        part_b_lines = []
        for line in attribute_lines_ids:
            if line.attribute_id.section == "part_b":
                part_b_lines.append(line)
            else:
                part_a_lines.append(line)
        return {
            "doc_ids": docids,
            "doc_model": "xe.student",
            "docs": docs,
            "data": data,
            "parent": parent,
            "part_a_lines": part_a_lines,
            "part_b_lines": part_b_lines,
        }
