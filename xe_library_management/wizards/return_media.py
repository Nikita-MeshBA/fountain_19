# -*- coding: utf-8 -*-

from odoo.exceptions import UserError

from odoo import models, fields, api, _


class ReturnMedia(models.TransientModel):
    """Return Media Wizard"""

    _name = "return.media"
    _description = "Return Media"

    media_id = fields.Many2one("xe.media", readonly=True)
    media_unit_id = fields.Many2one("xe.media.unit", required=True)
    actual_return_date = fields.Date(
        default=lambda self: fields.Date.today(), required=True
    )
    penalty = fields.Float()
    move_due_date = fields.Date("Return Date")

    def _get_days(self, to_date, from_date):
        to_date = fields.Datetime.from_string(to_date)
        from_date = fields.Datetime.from_string(from_date)
        return abs((from_date - to_date).days)

    @api.onchange("media_unit_id")
    def _get_due_date(self):
        date = False
        if self.media_unit_id:
            media_mov_obj = self.env["xe.media.movement"]
            unit = self.media_unit_id
            if unit:
                media_move = media_mov_obj.search(
                    [("media_unit_id", "=", unit.id), ("state", "=", "issue")]
                )
                date = media_move.return_date
        self.move_due_date = date

    @api.onchange("actual_return_date", "media_unit_id")
    def calculate_penalty(self):
        penalty_amt = 0
        if self.actual_return_date and self.media_unit_id:
            penalty_days = 0
            media_mov_obj = self.env["xe.media.movement"]
            unit = self.media_unit_id
            media_move = media_mov_obj.search(
                [("media_unit_id", "=", unit.id), ("state", "=", "issue")]
            )
            if media_move:
                standard_diff = self._get_days(
                    media_move.return_date, media_move.issued_date
                )
                actual_diff = self._get_days(
                    self.actual_return_date, media_move.issued_date
                )
                if (
                    media_move.library_card_id
                    and media_move.library_card_id.library_card_type_id
                ):
                    penalty_days = (
                        actual_diff > standard_diff
                        and actual_diff - standard_diff
                        or penalty_days
                    )
                    penalty_amt = (
                        penalty_days
                        * media_move.library_card_id.library_card_type_id.penalty_amt_per_day
                    )
            self.penalty = penalty_amt

    def create_penalty_invoice(self):
        for rec in self:
            account_id = False
            # product = self.env.ref('xe_library_management.xe_product_7')
            media_mov_obj = self.env["xe.media.movement"]
            unit = self.media_unit_id
            media_move = media_mov_obj.search(
                [("media_unit_id", "=", unit.id), ("state", "=", "issue")]
            )
            card = media_move.library_card_id
            product = card.library_card_type_id.product_id
            if product.id:
                account_id = product.property_account_income_id.id
            if not account_id:
                account_id = product.categ_id.property_account_income_categ_id.id
            if not account_id:
                raise UserError(
                    _(
                        f"There is no income account defined for this "
                        f"product: {product.name}. You may have to install a chart of "
                        f"account from Accounting app, settings menu."
                    )
                )
            invoice = self.env["account.move"].create(
                {
                    "partner_id": media_move.student_id.partner_id.id,
                    "move_type": "out_invoice",
                    "invoice_date": fields.Date.today(),
                    # 'account_id': self.student_id.partner_id.property_account_receivable_id.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": product.name,
                                "account_id": account_id,
                                "price_unit": self.penalty,
                                "quantity": 1.0,
                                "discount": 0.0,
                                "product_id": product.id,
                            },
                        )
                    ],
                }
            )
            media_move.write({"invoice_id": invoice.id})

    def do_return(self):
        for media in self:
            if media.media_unit_id.state and media.media_unit_id.state == "issue":
                media_move_search = self.env["xe.media.movement"].search(
                    [
                        ("media_unit_id", "=", media.media_unit_id.id),
                        ("state", "=", "issue"),
                    ]
                )
                if not media_move_search:
                    raise UserError(_("Can't return media."))
                if media.penalty:
                    media.create_penalty_invoice()
                media_move_search.return_media(media.actual_return_date)
            else:
                raise UserError(
                    _(
                        f"Media Unit can not be returned because it's state is : "
                        f"{dict(media.media_unit_id._fields['state'].selection).get(media.media_unit_id.state)}"
                    )
                )
