# pylint: disable=E0401,C0114,C0115
from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_dtb_journal = fields.Boolean(string="DTB Journal")
