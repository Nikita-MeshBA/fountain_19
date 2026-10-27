""" Hostel Member Leaves python file """
# pylint: disable= E0401, R0903, C0116
from odoo import models, fields, api, _


class HostelMemberLeaves(models.Model):
    """Hostel Member Leaves class"""

    _name = "xe.hostel.member_leaves"
    _inherit = ["mail.thread"]
    _description = "Hostel Member Leaves"
    _rec_name = "request_id"

    request_id = fields.Char(default="New", tracking=True)
    hostel_admission_id = fields.Many2one("xe.hostel.admission", tracking=True)
    hostel_id = fields.Many2one(
        "xe.hostel", related="hostel_admission_id.hostel_id", tracking=True
    )
    date_from = fields.Datetime(tracking=True)
    date_to = fields.Datetime(tracking=True)
    reason = fields.Char(tracking=True)
    days = fields.Char(compute="_compute_number_of_days", tracking=True)
    state = fields.Selection(
        [
            ("draft", "To Submit"),
            ("confirm", "To Approve"),
            ("validate", "Approved"),
            ("refuse", "Refused"),
        ],
        default="draft",
        tracking=True,
    )

    @api.model
    def create(self, vals):
        vals["request_id"] = self.env["ir.sequence"].next_by_code(
            "xe.hostel.member_leaves"
        ) or _("New")
        result = super(HostelMemberLeaves, self).create(vals)
        return result

    @api.depends("date_from", "date_to")
    def _compute_number_of_days(self):
        for rec in self:
            days_str = ""
            time_diff = rec.date_to - rec.date_from
            if time_diff:
                seconds = time_diff.days * 24 * 3600 + time_diff.seconds
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                if days:
                    days_str += "%d Days" % (days)
                if hours:
                    days_str += " %d Hours" % (hours)
                if minutes:
                    days_str += " %d Minutes" % (minutes)
                if seconds:
                    days_str += " %d Seconds" % (seconds)
            rec.days = days_str

    def button_submit(self):
        self.state = "confirm"

    def button_approve(self):
        self.state = "validate"

    def button_refuse(self):
        self.state = "refuse"
