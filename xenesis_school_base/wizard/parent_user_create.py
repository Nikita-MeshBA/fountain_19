from odoo.exceptions import ValidationError

from odoo import api, fields, models, _


class ParentUser(models.TransientModel):
    _name = "xe.parent.user"
    _description = "User Create For Parent"

    parent_ids = fields.Many2many("xe.parent")

    @api.model
    def default_get(self, fields):
        res = super(ParentUser, self).default_get(fields)
        active_ids = self.env.context.get("active_ids", []) or []
        res.update({"parent_ids": [(6, 0, active_ids)]})
        return res

    def create_user(self):
        parent_user_group = self.env.ref("xenesis_school_base.group_xe_parent")
        active_ids = self.env.context.get("active_ids", []) or []
        records = self.env["xe.parent"].browse(active_ids)
        for parent in records:
            user_obj = self.env["res.users"].search(
                [("login", "=", parent.email)], limit=1
            )

            if user_obj:
                raise ValidationError(
                    _(
                        "User already existing with the following parent: %s.",
                        parent.name,
                    )
                )

            # if not parent.user_id:
            if not user_obj:
                vals = {
                    "name": parent.name,
                    "login": parent.email,
                    "partner_id": parent.partner_id.id,
                }

                balance_group = self.env["res.groups"].search(
                    [("name", "=", "Balance on Student Profile")]
                )
                show_balance = "in_group_" + str(balance_group.id)
                popup_group = self.env["res.groups"].search(
                    [("name", "=", "Disable Many2one Popup Parent")]
                )
                disable_popup = "in_group_" + str(popup_group.id)
                hide_action = self.env["res.groups"].search(
                    [("name", "=", "Hide Action Menu")]
                )
                hide_action_group = "in_group_" + str(hide_action.id)
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

                vals[s_g] = self.env["res.groups"].search([("name", "=", "Parent")]).id
                if hide_action:
                    vals[hide_action_group] = hide_action.id
                if balance_group:
                    vals[show_balance] = balance_group.id
                if popup_group:
                    vals[disable_popup] = popup_group.id
                user_id = self.env["res.users"].create(vals)
                parent.user_id = user_id
                parent_user_group.users = parent_user_group.users + user_id
