# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    user_type = fields.Selection(
        [
            ("student", "Student"),
            ("teacher", "Teacher"),
            ("parent", "Parent"),
        ],
    )
    roll_number = fields.Char("Admission Number", compute="_compute_get_roll_number")
    total_balance_partner = fields.Monetary(
        string="Balance", compute="_compute_partner_balance"
    )

    def get_account_move_lines(self, partner_ids):
        # self.env.cr.execute(
        #     "SELECT m.name AS move_id, l.date, l.name, l.ref, l.date_maturity, \
        #     l.partner_id, l.blocked, l.amount_currency, l.currency_id, "
        #     "CASE WHEN at.type = 'receivable' "
        #     "THEN SUM(l.debit) "
        #     "ELSE SUM(l.credit * -1) "
        #     "END AS debit, "
        #     "CASE WHEN at.type = 'receivable' "
        #     "THEN SUM(l.credit) "
        #     "ELSE SUM(l.debit * -1) "
        #     "END AS credit, "
        #     "CASE WHEN l.date_maturity < %s "
        #     "THEN SUM(l.debit - l.credit) "
        #     "ELSE 0 "
        #     "END AS mat "
        #     "FROM account_move_line l "
        #     "JOIN account_account aa ON (l.account_id = aa.id) "
        #     "JOIN account_account_type at ON (aa.user_type_id = at.id) "
        #     "JOIN account_move m ON (l.move_id = m.id) "
        #     "WHERE l.partner_id IN %s AND at.type IN ('receivable', 'payable') \
        #     AND m.state='posted' AND l.full_reconcile_id IS NULL GROUP BY l.date, \
        #     l.name, l.ref, l.date_maturity, l.partner_id, at.type, l.blocked, \
        #     l.amount_currency, l.currency_id, l.move_id, m.name",
        #     ((fields.date.today(),) + (tuple(partner_ids),)),
        # )
        # result = self.env.cr.dictfetchall()
        # return result
        self.env.cr.execute(
            "SELECT m.name AS move_id, l.date, l.name, l.ref, l.date_maturity, \
            l.partner_id, l.blocked, l.amount_currency, l.currency_id, "
            "CASE WHEN aa.account_type = 'asset_receivable' "
            "THEN SUM(l.debit) "
            "ELSE SUM(l.credit * -1) "
            "END AS debit, "
            "CASE WHEN aa.account_type = 'asset_receivable' "
            "THEN SUM(l.credit) "
            "ELSE SUM(l.debit * -1) "
            "END AS credit, "
            "CASE WHEN l.date_maturity < %s "
            "THEN SUM(l.debit - l.credit) "
            "ELSE 0 "
            "END AS mat "
            "FROM account_move_line l "
            "JOIN account_account aa ON (l.account_id = aa.id) "
            "JOIN account_move m ON (l.move_id = m.id) "
            "WHERE l.partner_id IN %s AND aa.account_type IN ('asset_receivable', 'liability_payable') \
            AND m.state='posted' AND l.full_reconcile_id IS NULL GROUP BY l.date, \
            l.name, l.ref, l.date_maturity, l.partner_id, aa.account_type, l.blocked, \
            l.amount_currency, l.currency_id, l.move_id, m.name",
            ((fields.date.today(),) + (tuple(partner_ids),)),
        )
        result = self.env.cr.dictfetchall()
        return result

    def _compute_partner_balance(self):
        for rec in self:
            partner_id = rec.id
            lines = []
            if partner_id:
                lines = rec.get_account_move_lines([partner_id])
            debit = 0
            credit = 0
            for line in lines:
                if line["move_id"]:
                    debit = debit + line["debit"]
                    credit = credit + line["credit"]
            balance = debit - credit
            rec.total_balance_partner = balance

    @api.depends("user_type")
    def _compute_get_roll_number(self):
        roll_no = False
        for rec in self:
            if rec.user_type == "student":
                student = self.env["xe.student"].search([("partner_id", "=", rec.id)])
                if student:
                    roll_no = student.roll_number
            rec.roll_number = roll_no

    def _invoice_total(self):
        # results = super(ResPartner, self)._invoice_total()
        for record in self:
            record.total_invoiced = 0
            if not record.ids:
                return True

            all_partners_and_children = {}
            all_partner_ids = []
            for partner in record.filtered("id"):
                # price_total is in the company currency
                all_partners_and_children[partner] = (
                    record.with_context(active_test=False)
                    .search([("id", "child_of", partner.id)])
                    .ids
                )
                all_partner_ids += all_partners_and_children[partner]
            domain = [
                ("partner_id", "in", all_partner_ids),
                # ('state', 'not in', ['draft', 'cancel']),
                # ("move_type", "in", ("out_invoice", "out_refund")),
                ("move_type", "=", "out_invoice"),
            ]
            invoice_ids = self.env["account.move"].search(domain)
            record.total_invoiced = sum(inv.amount_total for inv in invoice_ids)


class ResGroups(models.Model):
    _inherit = "res.groups"

    def get_application_groups(self, domain):
        """Return the non-share groups that satisfy ``domain``."""
        group_popup_disable_stud = self.env.ref(
            "xenesis_school_base.group_popup_disable_stud"
        ).id
        group_popup_disable_parent = self.env.ref(
            "xenesis_school_base.group_popup_disable"
        ).id
        return self.search(
            domain
            + [("id", "not in", (group_popup_disable_stud, group_popup_disable_parent))]
        )


class Menu(models.Model):
    _inherit = "website.menu"

    # Temporary field to avoid issue in migrated db
    group_ids = fields.Many2many("res.groups", string="Groups")


class ResUsers(models.Model):
    _inherit = "res.users"

    def _cron_assign_studdent_page(self):
        usersr = self.env['res.users'].search([("action_id", '=', None)])
        for single_user in usersr:
            if single_user.has_group('xenesis_school_base.group_xe_parent'):
                single_user.write({"action_id": self.env.ref("xenesis_school_base.act_student").id})

    @api.model
    def create(self, values):
        res = super(ResUsers, self).create(values)
        if not res.action_id:
            if res.has_group('xenesis_school_base.group_xe_parent'):
                res.update({"action_id": self.env.ref("xenesis_school_base.act_student").id})
        return res
