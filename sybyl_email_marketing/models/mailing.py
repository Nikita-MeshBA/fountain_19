# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MassMailingListInherit(models.Model):
    _inherit = "mailing.list"

    is_public = fields.Boolean(
        default=False,
        help="The mailing list can be accessible by recipient in the unsubscription"
        " page to allows him to update his subscription preferences.",
    )
    mailing_type = fields.Selection(
        [("class", "Class"), ("classroom", "Classroom")], default="class"
    )
    class_ids = fields.Many2many("xe.course")
    classroom_ids = fields.Many2many("xe.classroom")

    @api.onchange("mailing_type")
    def _onchange_mailing_type(self):
        if self.mailing_type == "class":
            self.classroom_ids = False
        if self.mailing_type == "classroom":
            self.class_ids = False

    def _get_partner_ids(self, class_ids=False, classroom_ids=False):
        partners = []
        student_ids = None
        if class_ids:
            student_ids = self.env["xe.student"].search(
                [("course_id", "in", class_ids.ids)]
            )
        if classroom_ids:
            student_ids = self.env["xe.student"].search(
                [("classroom_id", "in", classroom_ids.ids)]
            )

        if student_ids:
            for student in student_ids:
                if student.partner_id and student.partner_id.email:
                    partners.append(student.partner_id)

                if student.parent_ids:
                    for parent in student.parent_ids:
                        if parent.partner_id and parent.partner_id.email:
                            partners.append(parent.partner_id)
        return partners

    @api.model
    def create(self, vals):
        result = super(MassMailingListInherit, self).create(vals)

        # Class
        if result.mailing_type == "class" and result.class_ids:
            class_partner = self._get_partner_ids(
                class_ids=result.class_ids, classroom_ids=False
            )
            for c_partner in class_partner:
                c_mailing_contact_id = False
                if c_partner.email:
                    c_mailing_contact_id = self.env["mailing.contact"].search(
                        [("email", "=", c_partner.email)], limit=1
                    )
                if c_mailing_contact_id:
                    c_mailing_contact_id.list_ids = [(4, result.id)]
                else:
                    self.env["mailing.contact"].create(
                        {
                            "name": c_partner.name,
                            "email": c_partner.email,
                            "list_ids": [(4, result.id)],
                        }
                    )

        # Classroom
        if result.mailing_type == "classroom" and result.classroom_ids:
            classroom_partner = self._get_partner_ids(
                class_ids=False, classroom_ids=result.classroom_ids
            )
            for cc_partner in classroom_partner:
                cc_mailing_contact_id = False
                if cc_partner.email:
                    cc_mailing_contact_id = self.env["mailing.contact"].search(
                        [("email", "=", cc_partner.email)], limit=1
                    )
                if cc_mailing_contact_id:
                    cc_mailing_contact_id.list_ids = [(4, result.id)]
                else:
                    self.env["mailing.contact"].create(
                        {
                            "name": cc_partner.name,
                            "email": cc_partner.email,
                            "list_ids": [(4, result.id)],
                        }
                    )
        return result

    def write(self, vals):
        old_class_ids = False
        old_classroom_ids = False
        new_class_ids = False
        new_classroom_ids = False
        if self.mailing_type == "class" and self.class_ids:
            old_class_ids = self.class_ids
        if self.mailing_type == "classroom" and self.classroom_ids:
            old_classroom_ids = self.classroom_ids

        result = super(MassMailingListInherit, self).write(vals)

        if self.mailing_type == "class" and self.class_ids:
            new_class_ids = self.class_ids
        if self.mailing_type == "classroom" and self.classroom_ids:
            new_classroom_ids = self.classroom_ids

        # Class
        if vals.get("class_ids") and self.mailing_type == "class" and self.class_ids:
            # Remove list Id from contacts for Class
            if old_class_ids and new_class_ids:
                c_removed_list = list(set(old_class_ids.ids) - set(new_class_ids.ids))
                if c_removed_list:
                    c_removed_ids = self.env["xe.course"].browse(c_removed_list)
                    remove_class_partner = self._get_partner_ids(
                        class_ids=c_removed_ids, classroom_ids=False
                    )
                    for c_remove_partner in remove_class_partner:
                        c_remove_mailing_contact_id = False
                        if c_remove_partner.email:
                            c_remove_mailing_contact_id = self.env[
                                "mailing.contact"
                            ].search([("email", "=", c_remove_partner.email)], limit=1)
                        if c_remove_mailing_contact_id:
                            c_remove_mailing_contact_id.list_ids = [(3, self.id)]

            # Add list Id in contacts for Class
            for c_partner in self._get_partner_ids(
                class_ids=self.class_ids, classroom_ids=False
            ):
                c_mailing_contact_id = False
                if c_partner.email:
                    c_mailing_contact_id = self.env["mailing.contact"].search(
                        [("email", "=", c_partner.email)], limit=1
                    )
                if c_mailing_contact_id:
                    c_mailing_contact_id.list_ids = [(4, self.id)]
                else:
                    self.env["mailing.contact"].create(
                        {
                            "name": c_partner.name,
                            "email": c_partner.email,
                            "list_ids": [(4, self.id)],
                        }
                    )

        # Classroom
        if (
            vals.get("classroom_ids")
            and self.mailing_type == "classroom"
            and self.classroom_ids
        ):
            # Remove list Id from contacts for Classroom
            if old_classroom_ids and new_classroom_ids:
                cc_removed_list = list(
                    set(old_classroom_ids.ids) - set(new_classroom_ids.ids)
                )
                if cc_removed_list:
                    cc_removed_ids = self.env["xe.course"].browse(cc_removed_list)
                    remove_classroom_partner = self._get_partner_ids(
                        class_ids=False, classroom_ids=cc_removed_ids
                    )
                    for cc_remove_partner in remove_classroom_partner:
                        cc_remove_mailing_contact_id = False
                        if cc_remove_partner.email:
                            cc_remove_mailing_contact_id = self.env[
                                "mailing.contact"
                            ].search([("email", "=", cc_remove_partner.email)], limit=1)
                        if cc_remove_mailing_contact_id:
                            cc_remove_mailing_contact_id.list_ids = [(3, self.id)]

            # Add list Id in contacts for Classroom
            for cc_partner in self._get_partner_ids(
                class_ids=False, classroom_ids=self.classroom_ids
            ):
                cc_mailing_contact_id = False
                if cc_partner.email:
                    cc_mailing_contact_id = self.env["mailing.contact"].search(
                        [("email", "=", cc_partner.email)], limit=1
                    )
                if cc_mailing_contact_id:
                    cc_mailing_contact_id.list_ids = [(4, self.id)]
                else:
                    self.env["mailing.contact"].create(
                        {
                            "name": cc_partner.name,
                            "email": cc_partner.email,
                            "list_ids": [(4, self.id)],
                        }
                    )
        return result
