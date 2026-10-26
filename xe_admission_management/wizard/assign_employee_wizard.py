from odoo import fields, models


class AssignEmployeeWizard(models.TransientModel):
    _name = "assign.employee.wizard"
    _description = "Assign Employee"

    employee_id = fields.Many2one("hr.employee", string="Assigned To", required=True)

    def get_complete_form_url(self, action_id, menu_id, obj_id, model):
        base_url = str(self.env.user.partner_id.get_base_url())
        address = (
            str(base_url)
            + "/web#action="
            + str(action_id)
            + "&cids=1&id="
            + str(obj_id)
            + "&menu_id="
            + str(menu_id)
            + "&model="
            + model
            + "&view_type=form"
        )
        return address

    def action_ok(self):
        active_ids = self.env.context.get("active_ids", []) or []
        login_user_id = self.env.user and self.env.user.id
        admission_obj = self.env["xe.admission.enquiry"].browse(active_ids)
        action_id = (
            self.env["ir.actions.act_window"]
            .sudo()
            .search(
                [("name", "=", "Enquiries"), ("res_model", "=", "xe.admission.enquiry")]
            )
            .id
        )
        menu_id = (
            self.env["ir.ui.menu"]
            .sudo()
            .search(
                [
                    ("name", "=", "Enquiries"),
                    ("complete_name", "=", "Admission/Enquiries"),
                ]
            )
            .id
        )
        model = "xe.admission.enquiry"

        form_complete_address = self.get_complete_form_url(
            action_id, menu_id, admission_obj.id, model
        )
        admission_obj.write(
            {
                "assigned_id": self.employee_id.id,
                "state": "assigned",
                "enq_url": form_complete_address,
            }
        )
        if self.employee_id.user_id:
            user_id = self.employee_id.user_id.id
        else:
            employee = self.employee_id
            employee.sudo().create_user()
            user_id = employee.user_id.id
        assigned_emp_user_id = (
            self.employee_id.user_id.id if self.employee_id.user_id else user_id
        )
        if login_user_id != assigned_emp_user_id:
            template = self.env.ref("xe_admission_management.mail_template_assign_emp")
            template.send_mail(admission_obj.id, force_send=True)
        return True
