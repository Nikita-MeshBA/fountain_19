from odoo import api, models


class OpStudent(models.Model):
    _inherit = "xe.student"

    def get_student_mobile(self):
        mobile = self.mobile or ""
        phone_code = self.partner_id.country_id.phone_code or ""
        if mobile and phone_code:
            tmp_mobile = mobile
            mobile = "+" + str(phone_code) + str(tmp_mobile)
        return mobile


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.onchange("country_id", "mobile")
    def _onchange_mobile(self):
        if self.mobile:
            if self.country_id and self.country_id.sms_mobile_prefix:
                if self.mobile.startswith("0"):
                    self.mobile = self.country_id.sms_mobile_prefix + self.mobile[
                        1:
                    ].replace(" ", "")
                elif self.mobile.startswith("+"):
                    self.mobile = self.mobile.replace(" ", "")
                else:
                    self.mobile = (
                        self.country_id.sms_mobile_prefix + self.mobile.replace(" ", "")
                    )
            else:
                self.mobile = self.mobile.replace(" ", "")

    def get_partner_mobile(self):
        mobile = self.mobile or ""
        phone_code = self.country_id.phone_code or ""
        if mobile and phone_code:
            tmp_mobile = mobile
            mobile = "+" + str(phone_code) + str(tmp_mobile)
        return mobile

    def get_mobile_numbers(self):
        mobile_numbers = []
        mobile = self.mobile or ""
        phone_code = self.country_id.phone_code or ""
        if mobile and not phone_code:
            mobile_numbers.append(mobile)
        if mobile and phone_code:
            tmp_mobile = mobile
            mobile = "+" + str(phone_code) + str(tmp_mobile)
            mobile_numbers.append(mobile)
        student = self.env["xe.student"].search([("partner_id", "=", self.id)])
        parents = self.env["xe.student.parent"].search(
            [("student_id", "=", student.id)]
        )
        parent_ids = parents.mapped("parent_id")
        if parent_ids:
            for parent in parent_ids:
                mobile = parent.partner_id.mobile or ""
                phone_code = parent.partner_id.country_id.phone_code or ""
                if mobile and not phone_code:
                    mobile_numbers.append(mobile)
                if mobile and phone_code:
                    tmp_mobile = mobile
                    p_mobile = "+" + str(phone_code) + str(tmp_mobile)
                    mobile_numbers.append(p_mobile)
        mobile_nos = ",".join(mobile_numbers)
        return mobile_nos
