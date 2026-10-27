import base64
import logging

from odoo.tools.safe_eval import safe_eval

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class SendEmailWizard(models.TransientModel):
    _name = "exam.send.email.wizard"

    def _get_active_ids(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    def _get_reportcard_tmpl(self):
        template = self.env.ref(
            "xe_exam_management.email_template_report_card_new", False
        )
        return template

    @api.depends("marksheet_line_ids")
    def _compute_get_line_count(self):
        count = 0
        if self.marksheet_line_ids:
            count = len(self.marksheet_line_ids)
        self.marksheet_line_count = count

    marksheet_line_ids = fields.Many2many(
        "xe.marksheet.line", string="Marksheet Lines", default=_get_active_ids
    )
    marksheet_line_count = fields.Integer(compute="_compute_get_line_count")
    email_template_id = fields.Many2one(
        "mail.template", string="Send Email Template", default=_get_reportcard_tmpl
    )
    template_body = fields.Text("Body", translate=True, help="Plain text of message")
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    report_template_id = fields.Many2one("ir.actions.report", "Report to attach")

    @api.onchange("email_template_id")
    def _set_template_body(self):
        if self.email_template_id:
            self.template_body = False
            self.template_body = self.email_template_id.body_html
            self.report_template_id = self.email_template_id.report_template_ids.ids
            report_domain = []
            report_domain.append(
                "|",
            )
            report_domain.append(
                ("id", "=", self.env.ref("xe_exam_management.report_marksheetline").id)
            )
            report_domain.append(
                "&",
            )
            report_domain.append(("model", "=", "xe.marksheet.line"))
            if self.env.user.has_group(
                "xe_exam_management.group_rubrics_configurations"
            ):
                report_domain.append(
                    (
                        "group_ids",
                        "in",
                        self.env.ref(
                            "xe_exam_management.group_rubrics_configurations"
                        ).ids,
                    )
                )
            if self.env.user.has_group(
                "xe_exam_management.group_subject_rubrics_configuration"
            ):
                report_domain.append(
                    (
                        "group_ids",
                        "in",
                        self.env.ref(
                            "xe_exam_management.group_subject_rubrics_configuration"
                        ).ids,
                    )
                )
            return {"domain": {"report_template_id": report_domain}}

    @api.onchange("report_template_id")
    def _change_attachments(self):
        if len(self.marksheet_line_ids) == 1:
            attachemnt_ids = []
            for obj in self.marksheet_line_ids:
                attachment_id = self._fetch_attachment(obj.id)
                if attachment_id:
                    attachemnt_ids.append(attachment_id)
            if attachemnt_ids:
                self.attachment_ids = [(6, 0, attachemnt_ids)]

    # def _fetch_attachment(self, obj):
    #     report = self.report_template_id
    #     if report:
    #         if report.print_report_name:
    #             report_name = safe_eval(report.print_report_name, {"object": obj})
    #         elif report.attachment:
    #             report_name = safe_eval(report.attachment, {"object": obj})
    #         else:
    #             report_name = "Document"
    #         filename = "%s.%s" % (report_name, "pdf")
    #         # pdf_bin, _ = report.sudo()._render_qweb_pdf([obj])
    #         pdf_bin, _ = report.sudo()._render_qweb_pdf(
    #             report_ref=report.report_name,
    #             res_ids=[obj],
    #         )
    #         attachment = self.env["ir.attachment"].create(
    #             {
    #                 "name": filename,
    #                 "datas": base64.b64encode(pdf_bin),
    #                 "res_model": "exam.send.email.wizard",
    #                 "res_id": self.id,
    #                 "type": "binary",  # override default_type from context, possibly meant for another model!
    #             }
    #         )
    #         return attachment.id
    #     else:
    #         return False

    def _fetch_attachment(self, obj_id):
        self.ensure_one()

        report = self.report_template_id
        if not report:
            return False

        report_name = "Document"

        if report.print_report_name:
            try:
                report_name = safe_eval(
                    report.print_report_name,
                    {"object": self.env["xe.marksheet.line"].browse(obj_id)},
                )
            except Exception:
                pass
        elif report.attachment:
            try:
                report_name = safe_eval(
                    report.attachment,
                    {"object": self.env["xe.marksheet.line"].browse(obj_id)},
                )
            except Exception:
                pass

        filename = f"{report_name}.pdf"

        pdf_bin, _ = report.sudo()._render_qweb_pdf(
            report_ref=report.report_name,
            res_ids=[obj_id],
        )

        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "datas": base64.b64encode(pdf_bin),
            "type": "binary",
            "mimetype": "application/pdf",
            "res_model": self._name,
            "res_id": self.id,
        })

        return attachment.id

    def action_send_mail(self):
        self.ensure_one()

        template = self.email_template_id
        if not template:
            raise UserError("Please select an email template.")

        for record in self.marksheet_line_ids:
            try:
                email_list = []

                # Student Email
                if record.student_id.partner_id.email:
                    email_list.append(record.student_id.partner_id.email)

                # Parent Emails
                for parent in record.student_id.parent_ids:
                    if parent.email:
                        email_list.append(parent.email)

                if not email_list:
                    _logger.warning(
                        "No email found for student %s", record.student_id.display_name
                    )
                    continue

                email_to = ",".join(email_list)

                # Generate attachment if required
                attachment_ids = self.attachment_ids.ids

                email_values = {
                    "email_to": email_to,
                    "attachment_ids": [(6, 0, attachment_ids)],
                }

                template.with_context(
                    mail=email_to,
                    custom_body=self.template_body,
                ).send_mail(
                    record.id,
                    email_values=email_values,
                    force_send=True,
                )

            except Exception:
                _logger.exception(
                    "Failed to send email for marksheet %s",
                    record.display_name,
                )

        return {"type": "ir.actions.act_window_close"}

    # def action_send_mail(self):
    #     multiple_report_template = self.email_template_id.report_template_ids[0].id
    #     for record in self.marksheet_line_ids:
    #         try:
    #             template = self.email_template_id
    #             template.body_html = self.template_body
    #             if self.attachment_ids:
    #                 template.attachment_ids = [(6, 0, self.attachment_ids.ids)]
    #                 report_name = template.report_name
    #                 report_template = template.report_template_ids.ids
    #                 # template.report_name = template.report_template_ids = [(5, 0, 0)]
    #                 template.report_name = False
    #                 template.report_template_ids = [(5, 0, 0)]
    #             else:
    #                 if template.report_template.id not in self.report_template_ids.ids:
    #                     template.report_template_ids = [(6, 0, [self.report_template_id.id])]
    #             email = []
    #             if record.student_id.partner_id.email:
    #                 email.append(record.student_id.partner_id.email)
    #             if record.student_id.parent_ids:
    #                 for parent in record.student_id.parent_ids:
    #                     if parent.email:
    #                         email.append(parent.email)
    #             email = ",".join(email)
    #             template.with_context(mail=email).send_mail(record.id, force_send=True)
    #             if self.attachment_ids:
    #                 template.report_name = report_name
    #                 template.report_template_ids = [(6, 0, report_template)]
    #                 template.attachment_ids = False
    #                 self.attachment_ids = False
    #         except Exception as e:
    #             _logger.info(e)
    #     self.email_template_id.report_template_ids = [(6, 0, [multiple_report_template])]
