# pylint: disable=E0401
from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_kcb_journal = fields.Boolean(string="KCB Journal")
