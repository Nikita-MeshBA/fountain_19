# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_mpesa_journal = fields.Boolean(string="Mpesa Journal")


class AccountPayment(models.Model):
    _inherit = "account.payment"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer/Vendor",
        store=True,
        readonly=False,
        ondelete="restrict",
        compute="_compute_partner_id",
        domain="['|','|',('parent_id','=', False), ('is_company','=', False) , ('is_company','=', True),('company_id','=', company_id)]",
        tracking=True,
        check_company=True,
    )
