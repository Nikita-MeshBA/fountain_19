# -*- coding: utf-8 -*-

from datetime import timedelta, date, datetime

from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _


class MediaTag(models.Model):
    _name = "xe.tag"
    _description = "Tag"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )


class XeMedia(models.Model):
    _name = "xe.media"
    _description = "Media"

    def _compute_total_units(self):
        for record in self:
            record.total_units = len(record.unit_ids.ids)

    name = fields.Char("Title", size=128, required=True)
    isbn = fields.Char("ISBN code / Barcode", size=64)
    tags_ids = fields.Many2many("xe.tag", string="Tag(s)")
    author_ids = fields.Many2many("xe.author", string="Author(s)", required=True)
    edition = fields.Char()
    description = fields.Text()
    publisher_ids = fields.Many2many(
        "xe.publisher", string="Publisher(s)", required=True
    )
    course_ids = fields.Many2many("xe.course", string="Class")
    movement_line_ids = fields.One2many("xe.media.movement", "media_id", "Movements")
    subject_ids = fields.Many2many("xe.subject", string="Subjects")
    internal_code = fields.Char(size=64)
    queue_ids = fields.One2many("xe.media.queue", "media_id", "Media Queue")
    unit_ids = fields.One2many("xe.media.unit", "media_id", "Units")
    media_type_id = fields.Many2one("xe.media.type")

    total_units = fields.Integer(compute="_compute_total_units")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("isbn") and self.search([("isbn", "=", vals.get("isbn")), ("company_id", "=", self.env.company.id)]):
                raise ValidationError(
                    _("ISBN code %s already exists. ISBN code should be unique per media!" % (vals.get("isbn")))
                )
            if vals.get("internal_code") and self.search([("internal_code", "=", vals.get("internal_code")), ("company_id", "=", self.env.company.id)]):
                raise ValidationError(
                    _("Internal code %s already exists. Internal code should be unique per media!" % (vals.get("internal_code")))
                )
        return super(XeMedia, self).create(vals_list)

    def write(self, vals):
        if vals.get("isbn") and self.search([("isbn", "=", vals.get("isbn")), ("company_id", "=", self.env.company.id)]):
            raise ValidationError(
                _("ISBN code %s already exists. ISBN code should be unique per media!" % (vals.get("isbn")))
            )
        if vals.get("internal_code") and self.search([("internal_code", "=", vals.get("internal_code")), ("company_id", "=", self.env.company.id)]):
            raise ValidationError(
                _("Internal code %s already exists. Internal code should be unique per media!" % (vals.get("internal_code")))
            )
        return super(XeMedia, self).write(vals)

    def act_gen_media_units(self):
        wizard_view_id = self.env.ref("xe_library_management.generate_media_form")
        ctx = {}
        ctx.update({"default_media_id": self.id})
        action = {
            "name": _("Generate Media Units"),
            "view_mode": "form",
            "view_id": wizard_view_id.id,
            "res_model": "generate.media.units",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": ctx,
        }
        return action


class MediaMovement(models.Model):
    _name = "xe.media.movement"
    _inherit = "mail.thread"
    _description = "Media Movement"
    _rec_name = "media_id"

    media_id = fields.Many2one("xe.media", required=True)
    media_unit_id = fields.Many2one("xe.media.unit", required=True, tracking=True)
    type = fields.Selection(
        [("student", "Student"), ("faculty", "Teacher")],
        "Student/Teacher",
        required=True,
    )
    student_id = fields.Many2one("xe.student")
    faculty_id = fields.Many2one(
        "hr.employee", domain="[('teach_type','=','teaching')]", string="Teacher"
    )
    library_card_id = fields.Many2one("xe.library.card", required=True, tracking=True)
    issued_date = fields.Date(required=True, default=fields.Date.today())
    return_date = fields.Date("Due Date", required=True)
    actual_return_date = fields.Date()
    penalty = fields.Float()
    partner_id = fields.Many2one("res.partner", "Person", tracking=True)
    reserver_name = fields.Char("Person Name", size=256)
    state = fields.Selection(
        [
            ("available", "Available"),
            ("reserve", "Reserved"),
            ("issue", "Issued"),
            ("renew", "Renew"),
            ("lost", "Lost"),
            ("return", "Returned"),
            ("return_done", "Returned Done"),
        ],
        "Status",
        default="available",
        tracking=True,
    )
    media_type_id = fields.Many2one(related="media_id.media_type_id", store=True)
    user_id = fields.Many2one("res.users", related="student_id.user_id", string="Users")
    invoice_id = fields.Many2one("account.move", readonly=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    def _get_days(self, to_date, from_date):
        to_date = fields.Datetime.from_string(to_date)
        from_date = fields.Datetime.from_string(from_date)
        return abs((from_date - to_date).days)

    @api.constrains("issued_date", "actual_return_date")
    def _check_actual_return_date(self):
        if self.actual_return_date:
            if self.issued_date > self.actual_return_date:
                raise UserError(
                    _("Actual Return Date cannot be set before Issued Date")
                )

    def get_diff_day(self):
        for media_mov_id in self:
            today_date = datetime.strptime(fields.Date.today(), "%Y-%m-%d")
            return_date = datetime.strptime(media_mov_id.return_date, "%Y-%m-%d")
            diff = today_date - return_date
            return abs(diff.days)

    @api.constrains("issued_date", "return_date")
    def _check_issue_n_return_dates(self):
        if self.issued_date > self.return_date:
            raise UserError(_("Return Date cannot be set before Issued Date."))

    @api.onchange("media_unit_id")
    def onchange_media_unit_id(self):
        self.state = self.media_unit_id.state
        self.media_id = self.media_unit_id.media_id

    @api.onchange("library_card_id")
    def onchange_library_card_id(self):
        if self.library_card_id and self.library_card_id.type == "others":
            self.type = "faculty"
        else:
            self.type = self.library_card_id.type
        self.student_id = self.library_card_id.student_id.id
        self.faculty_id = self.library_card_id.faculty_id.id
        self.return_date = date.today() + timedelta(
            days=self.library_card_id.library_card_type_id.duration
        )

    def issue_media(self):
        """function to issue media"""
        for record in self:
            if record.media_unit_id.state and record.media_unit_id.state == "available":
                record.media_unit_id.state = "issue"
                record.state = "issue"

    def return_media(self, return_date):
        for record in self:
            if not return_date:
                return_date = fields.Date.today()
            record.actual_return_date = return_date
            record.calculate_penalty()
            if record.penalty > 0.0:
                record.state = "return"
            else:
                record.state = "return_done"
            record.media_unit_id.state = "available"

    def calculate_penalty(self):
        for record in self:
            penalty_amt = 0
            penalty_days = 0
            standard_diff = self._get_days(record.return_date, record.issued_date)
            actual_diff = self._get_days(record.actual_return_date, record.issued_date)
            if record.library_card_id and record.library_card_id.library_card_type_id:
                penalty_days = (
                    actual_diff > standard_diff
                    and actual_diff - standard_diff
                    or penalty_days
                )
                penalty_amt = (
                    penalty_days
                    * record.library_card_id.library_card_type_id.penalty_amt_per_day
                )
            record.write({"penalty": penalty_amt})

    def create_penalty_invoice(self):
        for rec in self:
            account_id = False
            # product = self.env.ref('xe_library_management.xe_product_7')
            product = self.library_card_id.library_card_type_id.product_id
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
                    "partner_id": self.student_id.partner_id.id,
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
            self.invoice_id = invoice.id
