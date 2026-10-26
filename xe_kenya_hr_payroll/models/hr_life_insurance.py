from odoo import api, fields, models


class LifeInsurance(models.Model):
    _name = "hr.life.insurance"
    _description = "Life Insurance"

    @api.depends("amount", "duration")
    def _compute_premium(self):
        for insurance in self.filtered(lambda ins: not ins.duration):
            insurance.amount_premium = (
                insurance.amount / float(insurance.duration) or 0.0
            )

    employee_id = fields.Many2one("hr.employee", string="Employee")
    name = fields.Char(required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    amount = fields.Monetary()
    amount_premium = fields.Monetary(
        string="Premium", compute="_compute_premium", store=True
    )
    duration = fields.Integer(default=1)
    deduction_applied = fields.Integer()
