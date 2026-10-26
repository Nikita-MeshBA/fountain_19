# pylint: disable=E0401,C0114,C0115

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class XeTimings(models.Model):
    _name = "xe.timings"
    _inherit = ["mail.thread"]
    _description = "Timings"

    @api.depends("start_time", "end_time")
    def _compute_get_duration(self):
        for line in self:
            if line.end_time and line.start_time:
                line.duration = line.end_time - line.start_time

    name = fields.Char(tracking=True)
    start_time = fields.Float(tracking=True)
    end_time = fields.Float(tracking=True)
    duration = fields.Float(compute="_compute_get_duration", store=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.constrains("start_time", "end_time")
    def _check_time(self):
        for line in self:
            if line.end_time > 24 or line.end_time < 0:
                raise UserError(_("Invalid End Time"))
            if line.start_time > 24 or line.start_time < 0:
                raise UserError(_("Invalid Start Time"))
            if line.start_time > line.end_time:
                raise UserError(_("Start Time should be less than End Time"))
