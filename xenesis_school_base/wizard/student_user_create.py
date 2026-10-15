from odoo.exceptions import ValidationError

from odoo import api, fields, models, _


class StudentUser(models.TransientModel):
    _name = "xe.student.user"
    _description = "User Create For Student"

    student_ids = fields.Many2many("xe.student")

    @api.model
    def default_get(self, fields_list):
        res = super(StudentUser, self).default_get(fields_list)
        active_ids = self.env.context.get("active_ids", []) or []
        res.update({"student_ids": [(6, 0, active_ids)]})
        return res

    def create_user(self):
        stud_user_group = self.env.ref("xenesis_school_base.group_xe_student")
        active_ids = self.env.context.get("active_ids", []) or []
        records = self.env["xe.student"].browse(active_ids)
        for stud in records:
            if not stud.email:
                raise ValidationError(
                    _(
                        "Following student have not email: %s",
                        stud.name,
                    )
                )
            user_obj = self.env["res.users"].search(
                [("login", "=", stud.email)], limit=1
            )

            if user_obj:
                for parent_id in self.student_ids.parent_ids:
                    parent_id.write({"student_user_ids": [(6, 0, user_obj.ids)]})
                raise ValidationError(
                    _(
                        "User already existing with the following student: %s.",
                        stud.name,
                    )
                )

            if not user_obj:
                vals = {
                    "name": stud.name,
                    "login": stud.email,
                    "partner_id": stud.partner_id.id,
                }

                balance_group = self.env["res.groups"].search(
                    [("name", "=", "Balance on Student Profile")]
                )
                show_balance = "in_group_" + str(balance_group.id)
                hide_action = self.env["res.groups"].search(
                    [("name", "=", "Hide Action Menu")]
                )
                hide_action_group = "in_group_" + str(hide_action.id)
                popup_group = self.env["res.groups"].search(
                    [("name", "=", "Disable Many2one Popup Student")]
                )
                disable_popup = "in_group_" + str(popup_group.id)
                school_category_ids = self.env["res.groups"].search(
                    [("name", "in", ["Student", "Parent", "Teacher", "Admin"])]
                )
                s_g = "sel_groups_" + "_".join(
                    str(its) for its in sorted(school_category_ids.ids)
                )

                for i in self.env.user.groups_id.category_id:
                    groups = (
                        self.env["res.groups"]
                        .sudo()
                        .search([("category_id", "=", i.id)])
                    )
                    new_group = "sel_groups_" + "_".join(
                        str(it) for it in sorted(groups.ids)
                    )
                    vals[new_group] = False

                if hide_action:
                    vals[hide_action_group] = hide_action.id
                if balance_group:
                    vals[show_balance] = balance_group.id
                if popup_group:
                    vals[disable_popup] = popup_group.id
                vals[s_g] = self.env["res.groups"].search([("name", "=", "Student")]).id

                user_id = self.env["res.users"].create(vals)
                stud.user_id = user_id
                stud_user_group.users = stud_user_group.users + user_id
                for parent_id in self.student_ids.parent_ids:
                    parent_id.write({"student_user_ids": [(6, 0, user_id.ids)]})
