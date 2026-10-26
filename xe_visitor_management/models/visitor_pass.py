# -*- coding: utf-8 -*-

from odoo import models, fields, api


class VisitorPass(models.Model):
    _name = "visitor.pass"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "pass_number"
    _description = "Visitor Type"

    pass_number = fields.Char("Pass No.", readonly=True)
    name = fields.Char(required=True)
    phone = fields.Char()
    email = fields.Char()
    street = fields.Char(size=256)
    street2 = fields.Char(size=256)
    city = fields.Char(size=64)
    po_box_no = fields.Char("P.O. Box No.", size=8)
    meeting_with_id = fields.Many2one("hr.employee", "Meeting With", required=True)
    document_type_id = fields.Many2one(
        "document.type", string="Document Type", required=False
    )
    document_number = fields.Char(required=False)
    visitor_in_time = fields.Datetime(readonly=True, tracking=True)
    visitor_out_time = fields.Datetime(readonly=True, tracking=True)
    vehicle_number = fields.Char()
    approved_by_id = fields.Many2one(
        "res.users", "Approved By", readonly=True, tracking=True
    )
    duty_officer_name_id = fields.Many2one(
        "res.users",
        "Reception Duty Officer",
        required=True,
        default=lambda self: self.env.user.id,
    )
    purpose_type_id = fields.Many2one("purpose.type", "Purpose Type", required=True)
    purpose = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("visitor_in", "Visitor In"),
            ("approve_visitor", "Approve Visitor"),
            ("visitor_out", "Visitor Out"),
            ("done", "Done"),
        ],
        default="draft",
        tracking=True,
    )

    @api.model
    def create(self, vals):
        x = self.env["ir.sequence"].next_by_code("visitor.pass") or "/"
        vals["pass_number"] = x
        return super(VisitorPass, self).create(vals)

    def action_visitor_in(self):
        for record in self:
            template = self.env.ref(
                "xe_visitor_management.email_template_visitor_pass",
                raise_if_not_found=False,
            )
            template.send_mail(record.id)
            record.visitor_in_time = fields.Datetime.now()
        self.state = "visitor_in"

    def action_approve_visitor(self):
        for record in self:
            record.sudo().write(
                {"approved_by_id": self.env.uid, "state": "approve_visitor"}
            )

    def action_visitor_out(self):
        for record in self:
            record.visitor_out_time = fields.Datetime.now()
            self.state = "visitor_out"

    def action_done(self):
        self.state = "done"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    otp = fields.Boolean(string="Mobile Authentication Notification")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        res.update(otp=get_param("xe_visitor_management.otp"))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("xe_visitor_management.otp", self.otp)
