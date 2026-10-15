from odoo import fields, models


class CertificateWizard(models.TransientModel):
    _name = "xe.certificate.wizard"
    _description = "Leave Certificate Wizard"

    student_id = fields.Many2one("xe.student")
    line_ids = fields.Many2many("xe.certificate.atts.lines","xe_cert_rel", "lid", "cid", string="Attributes")
    att_line_ids = fields.One2many("xe.certificate.atts.lines","cid", string="Attributes")
    leaving_date = fields.Date(related="student_id.leaving_date")
    enrolled_course_id = fields.Many2one("xe.course", "Enrolled class/grade")

    def action_generation_leave_s(self):
        if self.student_id.gender == "female":
            gender = "She"
        else:
            gender = "He"
        data = {
            "model_id": self.id,
            "gender": gender,
            "attribute_lines_ids": self.line_ids.ids,
            "attribute_lines": self.att_line_ids.ids,
            "leaving_date": self.leaving_date.strftime("%d-%m-%Y"),
            "enrolled_course": self.enrolled_course_id.name,
        }
        docids = self.student_id.ids
        data["docids"] = docids
        return self.env.ref(
            "xenesis_school_base.action_leaving_certificate_report"
        ).report_action(docids, data=data)


class CertificateWizardLines(models.TransientModel):
    _name = "xe.certificate.atts.lines"
    _description = "Leave Certificate Attribute Lines"

    cid = fields.Many2one("xe.certificate.wizard", "Cert")
    attribute_id = fields.Many2one("leave.certificate.attribute", "Attribute")
    value = fields.Char()
