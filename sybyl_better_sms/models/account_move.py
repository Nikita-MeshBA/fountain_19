from odoo import api, models, fields
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        result = super(AccountMove, self).action_post()
        if self.move_type == "out_invoice":
            sms_alert_rec = self.env["xe.send.sms.config"].search(
                [("active", "=", True)]
            )
            default_invoice_validate = sms_alert_rec.is_invoice_validate
            if default_invoice_validate:
                for invoice in self:
                    mobiles = []
                    student_id = self.env["xe.student"].search(
                        [("partner_id", "=", invoice.partner_id.id)], limit=1
                    )
                    if student_id:
                        if student_id.mobile:
                            mobiles.append(student_id.mobile)
                        for parent in student_id.parent_ids:
                            if parent.mobile:
                                mobiles.append(parent.mobile)

                        send_sms_template = self.env["send.sms.template"]
                        sms_rendered_content = send_sms_template.render_template(
                            sms_alert_rec.invoice_validate_tmpl_id.template_body,
                            "account.move",
                            invoice.id,
                        )
                        rendered_msg_to = send_sms_template.render_template(
                            mobiles, "account.move", invoice.id
                        )
                        gateway_model = self.env["sms.gateway.config"].search(
                            [("active", "=", True)], limit=1
                        )
                        if (
                            "is_better_sms" in self.env["sms.gateway.config"]._fields
                            and gateway_model.is_better_sms
                        ):
                            template_id = (
                                sms_alert_rec.invoice_validate_tmpl_id.id
                                if sms_alert_rec.invoice_validate_tmpl_id
                                else False
                            )
                            active_model = self._name
                            gateway_model.better_send_sms(
                                sms_rendered_content,
                                mobiles
                            )
                        else:
                            gateway_model.send_sms(
                                rendered_msg_to, sms_rendered_content
                            )
        return result


class AccountPayments(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        """draft -> posted"""
        self.move_id._post(soft=False)
        self.filtered(
            lambda pay: pay.is_internal_transfer
            and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()

        if self.payment_type == "inbound":
            sms_alert_rec = self.env["xe.send.sms.config"].search(
                [("active", "=", True)]
            )
            default_invoice_validate = sms_alert_rec.is_payment
            if default_invoice_validate:
                for payment in self:
                    mobiles = []
                    student_id = self.env["xe.student"].search(
                        [("partner_id", "=", payment.partner_id.id)], limit=1
                    )
                    if student_id:
                        if student_id.mobile:
                            mobiles.append(student_id.mobile)
                        for parent in student_id.parent_ids:
                            if parent.mobile:
                                mobiles.append(parent.mobile)

                        send_sms_template = self.env["send.sms.template"]
                        sms_rendered_content = send_sms_template.render_template(
                            sms_alert_rec.payment_tmpl_id.template_body,
                            "account.payment",
                            payment.id,
                        )
                        rendered_msg_to = send_sms_template.render_template(
                            mobiles, "account.payment", payment.id
                        )
                        gateway_model = self.env["sms.gateway.config"].search(
                            [("active", "=", True)], limit=1
                        )

                        if (
                            "is_better_sms" in self.env["sms.gateway.config"]._fields
                            and gateway_model.is_better_sms
                        ):
                            template_id = (
                                sms_alert_rec.payment_tmpl_id.id
                                if sms_alert_rec.payment_tmpl_id
                                else False
                            )
                            active_model = self._name
                            gateway_model.better_send_sms(
                                sms_rendered_content,
                                mobiles
                            )
                        else:
                            gateway_model.send_sms(
                                rendered_msg_to, sms_rendered_content
                            )
