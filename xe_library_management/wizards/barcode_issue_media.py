# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo import models, fields, api, _


class BarcodeIssueMedia(models.TransientModel):
    """Issue Media"""

    _name = "barcode.issue.media"
    _description = "Barcode Issue Media"

    # @api.onchange('transaction_type', 'media_unit_number')
    # def _get_due_date(self):
    #     date = False
    #     if self.transaction_type == 'return' and self.actual_return_date and self.media_unit_number:
    #         media_mov_obj = self.env['xe.media.movement']
    #         media_unit = self.env['xe.media.unit']
    #         unit = media_unit.search([('barcode', '=', self.media_unit_number)])
    #         if unit:
    #             media_move = media_mov_obj.search(
    #                 [('media_unit_id', '=', unit.id), ('state', '=', 'issue')])
    #             date = media_move.return_date
    #     self.move_due_date = date

    transaction_type = fields.Selection(
        [("issue", "Issue"), ("return", "Return"), ("renew", "Renew Media")],
        default="issue",
    )
    student_id = fields.Many2one("xe.student")
    course_id = fields.Many2one("xe.course")
    classroom_id = fields.Many2one("xe.classroom")
    type = fields.Selection(related="library_card_id.type")
    media_unit_ids = fields.Many2many("xe.media.unit")
    # media_unit_number = fields.Char('Media Unit Number')
    # library_card_number = fields.Char('Library Card Number',
    #  help="Please add Student Admission Number / Employee Number")
    library_card_id = fields.Many2one(
        "xe.library.card", help="Please add Student Admission Number / Employee Number"
    )
    # issued_date = fields.Date(
    #     'Issued Date', default=fields.Date.today())
    # return_date = fields.Date('Return Date')
    # actual_return_date = fields.Date(
    #     'Actual Return Date', default=lambda self: fields.Date.today())
    # move_due_date = fields.Date('Return Date')
    # penalty = fields.Float()
    barcode_issue_media_line_ids = fields.One2many(
        "barcode.issue.media.lines", "barcode_issue_media_id"
    )

    # @api.onchange('issued_date','library_card_number')
    # def _set_return_date(self):
    #     if self.issued_date and self.library_card_number:
    #         library_card_obj = self.env['xe.library.card']
    #         card = library_card_obj.search(
    #             [('number', '=', self.library_card_number)])
    #         if not card:
    #             raise UserError('Please Enter a Valid Library Card Number')
    #         add_days = card.library_card_type_id.duration
    #         return_date = self.issued_date + timedelta(days=add_days)
    #         self.return_date = return_date

    # def check_max_issue(self, student_id, library_card_id):
    #     media_movement_search = self.env["xe.media.movement"].search(
    #         [('library_card_id', '=', library_card_id),
    #          ('student_id', '=', student_id),
    #          ('state', '=', 'issue')])
    #     if len(media_movement_search) < self.env["xe.library.card"].browse(
    #             library_card_id).library_card_type_id.allow_media:
    #         return True
    #     else:
    #         return False

    # def _get_days(self, to_date, from_date):
    #     to_date = fields.Datetime.from_string(to_date)
    #     from_date = fields.Datetime.from_string(from_date)
    #     return abs((from_date - to_date).days)

    # @api.onchange('actual_return_date', 'transaction_type', 'media_unit_number')
    # def calculate_penalty(self):
    #     penalty_amt = 0
    #     if self.transaction_type == 'return' and self.actual_return_date and self.media_unit_number:
    #         penalty_days = 0
    #         media_mov_obj = self.env['xe.media.movement']
    #         media_unit = self.env['xe.media.unit']
    #         unit = media_unit.search([('barcode', '=', self.media_unit_number)])
    #         if not unit:
    #             self.media_unit_number = False
    #             raise UserError('Please enter a Valid Media unit Number')
    #         media_move = media_mov_obj.search(
    #             [('media_unit_id', '=', unit.id), ('state', '=', 'issue')])
    #         if media_move:
    #             standard_diff = self._get_days(media_move.return_date, media_move.issued_date)
    #             actual_diff = self._get_days(self.actual_return_date, media_move.issued_date)
    #             if media_move.library_card_id and media_move.library_card_id.library_card_type_id:
    #                 penalty_days = actual_diff > standard_diff and actual_diff - standard_diff or penalty_days
    #                 penalty_amt = penalty_days * media_move.library_card_id.library_card_type_id.penalty_amt_per_day
    #         self.penalty = penalty_amt

    # def create_penalty_invoice(self):
    #     for rec in self:
    #         account_id = False
    #         # product = self.env.ref('xe_library_management.xe_product_7')
    #         media_mov_obj = self.env['xe.media.movement']
    #         media_unit = self.env['xe.media.unit']
    #         unit = media_unit.search([('barcode', '=', self.media_unit_number)])
    #         if not unit:
    #             self.media_unit_number = False
    #             raise UserError('Please enter a Valid Media unit Number')
    #         media_move = media_mov_obj.search(
    #             [('media_unit_id', '=', unit.id), ('state', '=', 'issue')])
    #         card = media_move.library_card_id
    #         product = card.library_card_type_id.product_id
    #         if product.id:
    #             account_id = product.property_account_income_id.id
    #         if not account_id:
    #             account_id = \
    #                 product.categ_id.property_account_income_categ_id.id
    #         if not account_id:
    #             raise UserError(
    #                 _('There is no income account defined for this \
    #                    product: "%s". You may have to install a chart of \
    #                    account from Accounting app, settings \
    #                    menu.') % (product.name,))

    #         invoice = self.env['account.move'].create({
    #             'partner_id': media_move.student_id.partner_id.id,
    #             'move_type': 'out_invoice',
    #             'invoice_date': fields.Date.today(),
    #             # 'account_id': self.student_id.partner_id.property_account_receivable_id.id,
    #             'invoice_line_ids': [(0, 0, {
    #                 'name': product.name,
    #                 'account_id': account_id,
    #                 'price_unit': self.penalty,
    #                 'quantity': 1.0,
    #                 'discount': 0.0,
    #                 'product_id': product.id,
    #             })],
    #         })
    #         media_move.write({'invoice_id': invoice.id})

    # def barcode_do_issue(self):
    #     library_card_obj = self.env['xe.library.card']
    #     media_mov_obj = self.env['xe.media.movement']
    #     media_unit = self.env['xe.media.unit']
    #     for media in self:
    #         unit = media_unit.search(
    #             [('barcode', '=', media.media_unit_number)])
    #         if not unit:
    #             raise UserError(_("Media Unit can not available : \
    #             %s") % (media.media_unit_number))
    #         elif media.transaction_type == 'return':
    #             media_move_search = media_mov_obj.search(
    #                 [('media_unit_id', '=', unit.id), ('state', '=', 'issue')])
    #             if not media_move_search:
    #                 raise UserError(_("Can't return media : %s") %
    #                                 (media.media_unit_number))
    #             if media.penalty:
    #                 media.create_penalty_invoice()
    #             media_move_search.return_media(media.actual_return_date)
    #         else:
    #             card = library_card_obj.search(
    #                 [('number', '=', media.library_card_number)])
    #             faculty_id = card.type == 'faculty' and \
    #                          card.faculty_id.id or False
    #             student_id = card.type == 'student' \
    #                          and card.student_id.id or False
    #             if not card:
    #                 raise UserError(_("Card not available : %s") %
    #                                 (media.library_card_number))
    #             elif media.check_max_issue(card.student_id.id, card.id):
    #                 if unit.state and \
    #                         unit.state == 'available':
    #                     media_movement_create = {
    #                         'media_id': unit.media_id.id,
    #                         'media_unit_id': unit.id,
    #                         'type': card.type,
    #                         'student_id': student_id,
    #                         'faculty_id': faculty_id,
    #                         'library_card_id': card.id,
    #                         'issued_date': fields.Date.today(),
    #                         'return_date': datetime.today() +
    #                                        relativedelta(
    #                                            days=card.library_card_type_id.duration),
    #                         'state': 'available',
    #                     }
    #                     movement = media_mov_obj.sudo().create(
    #                         media_movement_create)
    #                     movement.issue_media()
    #                 else:
    #                     raise UserError(_("Media Unit can not be issued \
    #                     because it's state is : %s") % (unit.state))
    #             else:
    #                 allow_media = card.library_card_type_id.allow_media
    #                 raise UserError(_(
    #                     'Maximum Number of media allowed for %s is : \
    #                     %s') % (card.student_id.name, allow_media))

    @api.onchange("transaction_type", "library_card_id")
    def _get_media_unit_ids(self):
        self.media_unit_ids = False
        media_unit_list = []
        if self.transaction_type == "issue":
            media_unit_ids = (
                self.env["xe.media.unit"].search([("state", "=", "available")]).ids
            )
            media_unit_list = media_unit_ids
        if self.transaction_type in ["return", "renew"]:
            media_unit_ids = (
                self.env["xe.media.movement"]
                .search(
                    [
                        ("state", "=", "issue"),
                        ("library_card_id", "=", self.library_card_id.id),
                    ]
                )
                .mapped("media_unit_id")
            )
            media_unit_list = media_unit_ids.ids
        self.media_unit_ids = [(6, 0, media_unit_list)]

    @api.onchange("library_card_id")
    def _onchange_library_card_id(self):
        self.student_id = False
        self.course_id = False
        self.classroom_id = False
        if self.library_card_id and self.library_card_id.type == "student":
            self.student_id = self.library_card_id.student_id.id
            self.course_id = self.library_card_id.course_id.id
            self.classroom_id = self.library_card_id.student_id.classroom_id or False

    def barcode_do_issue(self):
        library_card_obj = self.env["xe.library.card"]
        media_mov_obj = self.env["xe.media.movement"]
        media_unit = self.env["xe.media.unit"]
        for media_line in self.barcode_issue_media_line_ids:
            unit = media_unit.search(
                [("barcode", "=", media_line.media_unit_id.barcode)]
            )
            if not unit:
                raise UserError(
                    _("Media Unit can not available : %s")
                    % (media_line.media_unit_id.barcode)
                )
            elif self.transaction_type == "return":
                media_move_search = media_mov_obj.search(
                    [("media_unit_id", "=", unit.id), ("state", "=", "issue")]
                )
                if not media_move_search:
                    raise UserError(
                        _("Can't return media : %s")
                        % (media_line.media_unit_id.barcode)
                    )
                if media_line.penalty:
                    media_line.create_penalty_invoice()
                media_move_search.return_media(media_line.actual_return_date)
            else:
                card = library_card_obj.search(
                    [("number", "=", self.library_card_id.number)]
                )
                faculty_id = card.type == "others" and card.faculty_id.id or False
                student_id = card.type == "student" and card.student_id.id or False
                if not card:
                    raise UserError(
                        _("Card not available : %s") % (self.library_card_id.number)
                    )
                elif media_line.check_max_issue(card.student_id.id, card.id):
                    if unit.state and unit.state == "available":
                        media_movement_create = {
                            "media_id": unit.media_id.id,
                            "media_unit_id": unit.id,
                            "type": "faculty" if card.type == "others" else "student",
                            "student_id": student_id,
                            "faculty_id": faculty_id,
                            "library_card_id": card.id,
                            "issued_date": fields.Date.today(),
                            "return_date": datetime.today()
                            + relativedelta(days=card.library_card_type_id.duration),
                            "state": "available",
                        }
                        movement = media_mov_obj.sudo().create(media_movement_create)
                        movement.issue_media()
                    elif (
                        unit.state
                        and unit.state == "issue"
                        and self.transaction_type == "renew"
                    ):
                        movement_line_id = media_line.media_unit_id.movement_lines_ids[-1]
                        movement_line_id.state = "renew"
                        new_movement_id = movement_line_id.copy()
                        new_movement_id.write(
                            {
                                "issued_date": fields.Date.today(),
                                "return_date": datetime.today()
                                + relativedelta(
                                    days=card.library_card_type_id.duration
                                ),
                                "actual_return_date": False,
                                "state": "issue",
                            }
                        )
                    else:
                        raise UserError(
                            _("Media Unit can not be issued because it's state is : %s")
                            % (unit.state)
                        )
                elif (
                    unit.state
                    and unit.state == "issue"
                    and self.transaction_type == "renew"
                ):
                    movement_line_id = media_line.media_unit_id.movement_lines_ids[-1]
                    movement_line_id.state = "renew"
                    new_movement_id = movement_line_id.copy()
                    new_movement_id.write(
                        {
                            "issued_date": fields.Date.today(),
                            "return_date": datetime.today()
                            + relativedelta(days=card.library_card_type_id.duration),
                            "actual_return_date": False,
                            "state": "issue",
                        }
                    )
                else:
                    allow_media = card.library_card_type_id.allow_media
                    raise UserError(
                        _(
                            f"Maximum Number of media allowed for {card.student_id.name} is : {allow_media}"
                        )
                    )

    @api.onchange("transaction_type")
    def _onchange_transaction_type(self):
        if self.transaction_type:
            self.barcode_issue_media_line_ids = False


class BarcodeIssueMediaLines(models.TransientModel):
    """Issue Media Lines"""

    _name = "barcode.issue.media.lines"
    _description = "Barcode Issue Media Lines"

    barcode_issue_media_id = fields.Many2one("barcode.issue.media")
    domain_media_unit_ids = fields.Many2many(
        "xe.media.unit", compute="compute_domain_media_unit_ids"
    )
    media_unit_id = fields.Many2one("xe.media.unit")
    media_id = fields.Many2one("xe.media", related="media_unit_id.media_id")
    media_isbn = fields.Char(related="media_unit_id.media_isbn")
    issued_date = fields.Date(default=fields.Date.today())
    return_date = fields.Date()
    actual_return_date = fields.Date(default=lambda self: fields.Date.today())
    move_due_date = fields.Date("Return Date")
    penalty = fields.Float()

    @api.depends("barcode_issue_media_id")
    def compute_domain_media_unit_ids(self):
        for record in self:
            if (
                record.barcode_issue_media_id.barcode_issue_media_line_ids
                and len(record.barcode_issue_media_id.barcode_issue_media_line_ids) > 1
            ):
                allow_media_unit_ids = (
                    record.barcode_issue_media_id.media_unit_ids._origin
                )
                selected_media_unit_ids = (
                    record.barcode_issue_media_id.barcode_issue_media_line_ids[
                        :-1
                    ].mapped("media_unit_id")
                )
                record.domain_media_unit_ids = (
                    allow_media_unit_ids - selected_media_unit_ids
                ).ids
            else:
                record.domain_media_unit_ids = (
                    record.barcode_issue_media_id.media_unit_ids._origin.ids
                )

    @api.onchange("media_unit_id")
    def _get_due_date(self):
        date = False
        if (
            self.barcode_issue_media_id.transaction_type == "return"
            and self.actual_return_date
            and self.media_unit_id
        ):
            media_mov_obj = self.env["xe.media.movement"]
            media_unit = self.env["xe.media.unit"]
            unit = media_unit.search([("barcode", "=", self.media_unit_id.barcode)])
            if unit:
                media_move = media_mov_obj.search(
                    [("media_unit_id", "=", unit.id), ("state", "=", "issue")]
                )
                date = media_move.return_date
        self.move_due_date = date

    @api.onchange("issued_date")
    def _set_return_date(self):
        if self.issued_date and self.barcode_issue_media_id.library_card_id:
            library_card_obj = self.env["xe.library.card"]
            card = library_card_obj.search(
                [("number", "=", self.barcode_issue_media_id.library_card_id.number)]
            )
            if not card:
                raise UserError(_("Please Enter a Valid Library Card Number"))
            add_days = card.library_card_type_id.duration
            return_date = self.issued_date + timedelta(days=add_days)
            self.return_date = return_date

    def check_max_issue(self, student_id, library_card_id):
        media_movement_search = self.env["xe.media.movement"].search(
            [
                ("library_card_id", "=", library_card_id),
                ("student_id", "=", student_id),
                ("state", "=", "issue"),
            ]
        )
        if (
            len(media_movement_search)
            < self.env["xe.library.card"]
            .browse(library_card_id)
            .library_card_type_id.allow_media
        ):
            return True
        else:
            return False

    def _get_days(self, to_date, from_date):
        to_date = fields.Datetime.from_string(to_date)
        from_date = fields.Datetime.from_string(from_date)
        return abs((from_date - to_date).days)

    @api.onchange("actual_return_date", "media_unit_id")
    def calculate_penalty(self):
        penalty_amt = 0
        if (
            self.barcode_issue_media_id.transaction_type == "return"
            and self.actual_return_date
            and self.media_unit_id
        ):
            penalty_days = 0
            media_mov_obj = self.env["xe.media.movement"]
            media_unit = self.env["xe.media.unit"]
            unit = media_unit.search([("barcode", "=", self.media_unit_id.barcode)])
            if not unit:
                self.media_unit_id = False
                raise UserError(_("Please enter a Valid Media unit Number"))
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
            media_mov_obj = self.env["xe.media.movement"]
            media_unit = self.env["xe.media.unit"]
            unit = media_unit.search([("barcode", "=", self.media_unit_id.barcode)])
            if not unit:
                self.media_unit_id = False
                raise UserError(_("Please enter a Valid Media unit Number"))
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
                        'There is no income account defined for this \
                       product: "%s". You may have to install a chart of \
                       account from Accounting app, settings menu.'
                    )
                    % (product.name,)
                )

            invoice = self.env["account.move"].create(
                {
                    "partner_id": media_move.student_id.partner_id.id,
                    "move_type": "out_invoice",
                    "invoice_date": fields.Date.today(),
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
