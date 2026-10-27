from odoo.exceptions import UserError

from odoo import api, fields, models, _


class ResconfigInherit(models.TransientModel):
    _inherit = "res.config.settings"

    is_auto_session_name = fields.Boolean(
        "Auto concatenate exam session name",
        config_parameter="xe_exam_management.is_auto_session_name",
    )
    group_rubrics_configurations = fields.Boolean(
        "Generic Rubrics",
        config_parameter="xe_exam_management.group_rubrics_configurations",
        implied_group="xe_exam_management.group_rubrics_configurations",
        default=True,
    )
    group_subject_rubrics_configuration = fields.Boolean(
        "Exam Session wise Rubrics",
        config_parameter="xe_exam_management.group_subject_rubrics_configuration",
        implied_group="xe_exam_management.group_subject_rubrics_configuration",
    )
    show_marks_in_cbc_report = fields.Boolean(
        config_parameter="xe_exam_management.show_marks_in_cbc_report"
    )

    @api.constrains(
        "group_rubrics_configurations", "group_subject_rubrics_configuration"
    )
    def _check_exam_configure(self):
        if (
            self.group_rubrics_configurations
            and self.group_subject_rubrics_configuration
        ):
            raise UserError(
                _(
                    "You cant configure both Exam Session wise Rubrics and Generic Rubrics!!!"
                )
            )

    @api.model
    def get_values(self):
        res = super(ResconfigInherit, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        users = self.env["res.users"].search([])
        rubric_group_id = self.env.ref(
            "xe_exam_management.group_rubrics_configurations"
        )
        if not params.get_param(
            "xe_exam_management.group_rubrics_configurations"
        ) and not params.get_param(
            "xe_exam_management.group_subject_rubrics_configuration"
        ):
            res.update(group_rubrics_configurations=True)
            users -= rubric_group_id.users
            to_add = [
                (
                    4,
                    self.env.ref("xe_exam_management.group_rubrics_configurations").id,
                )
            ]
            users.write({"group_ids": to_add})
        else:
            if params.get_param(
                "xe_exam_management.group_subject_rubrics_configuration"
            ) and self.env.user.has_group(
                "xe_exam_management.group_rubrics_configurations"
            ):
                rubric_group_id.users.write(
                    {
                        "group_ids": [
                            (
                                3,
                                self.env.ref(
                                    "xe_exam_management.group_rubrics_configurations"
                                ).id,
                            )
                        ]
                    }
                )
        return res
