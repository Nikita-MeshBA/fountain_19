from odoo import fields, models


class ClearanceFormWizard(models.TransientModel):
    _name = "xe.clearance.form.wizard"
    _description = "Clearance Form"

    student_id = fields.Many2one("xe.student")
    index_no = fields.Char("Index Number")
    clearance_date = fields.Date("Date")
    attribute_lines_ids = fields.Many2many("xe.clearance.attribute.line")
    new_attribute_lines = fields.One2many("xe.clearance.attribute.line", "cid", string="Attribute Line")
    parent_id = fields.Many2one("xe.parent")

    def action_generation_clearance(self):
        data = {
            "model_id": self.id,
            "index_no": self.index_no,
            "clearance_date": self.clearance_date.strftime("%d-%m-%Y"),
            "attribute_lines_ids": self.attribute_lines_ids.ids,
            "attribute_lines": self.new_attribute_lines.ids,
            "parent_id": self.parent_id.id,
        }
        docids = self.student_id.ids
        data["docids"] = docids
        return self.env.ref(
            "xenesis_school_base.action_clearance_form_report"
        ).report_action(docids, data=data)


class ClearanceAttributeLines(models.TransientModel):
    _name = "xe.clearance.attribute.line"
    _description = "Clearance Attribute Lines"

    cid = fields.Many2one("xe.clearance.form.wizard")
    attribute_id = fields.Many2one("clearance.form.attributes", "Attribute")
    section = fields.Selection(related="attribute_id.section", string="Section")
    value = fields.Char()
