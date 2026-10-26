from odoo.exceptions import UserError

from odoo import models, fields, api, _


class XeSubject(models.Model):
    _inherit = "xe.subject"

    show_on_report_card = fields.Boolean("Show on Report", default=True)
    is_parent = fields.Boolean()
    hide_grade_on_report = fields.Boolean("Hide Grade on Report")
    parent_id = fields.Many2one(
        "xe.subject", "Parent Subject", domain=[("is_parent", "!=", False)]
    )
    sequence = fields.Integer()
    is_examinable = fields.Boolean(string="Examinable", default=True)

    @api.constrains("parent_id", "sequence", "is_parent")
    def _check_constraint(self):
        for record in self:
            is_parent = record.is_parent
            sequence = record.sequence
            if sequence == 0:
                raise UserError(_("You cannot assign Sequence 0, Start from 1"))
            parent_id = record.parent_id and record.parent_id.id or False
            if is_parent and parent_id:
                raise UserError(_("A parent subject cannot be have another parent"))

    @api.constrains("sequence", "company_id")
    def _check_duplicate_seq(self):
        for line in self:
            rec_count = self.search_count(
                [
                    ("company_id", "=", line.company_id.id),
                    ("sequence", "=", line.sequence),
                ]
            )
            if rec_count > 1:
                raise UserError(_("Sequence should be unique per subject!"))

    @api.onchange("is_parent")
    def _onchange_is_parent(self):
        if self.sequence and not self.is_parent:
            self.sequence = False
