# -*- coding: utf-8 -*-

from odoo.exceptions import UserError

from odoo import models, fields, api, _


class ProductRequest(models.Model):
    _name = "xe.product.request"
    _inherit = ["mail.thread"]
    _description = "Product Request"

    name = fields.Char(default="New")
    r_date = fields.Datetime(
        "Request Date", default=fields.Datetime.now(), tracking=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("request", "Requested"),
            ("accept_by_manager", "Accepted by Inventory Manager"),
            ("issue", "Issued"),
            ("return", "Returned"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user.id, string="Requested By"
    )
    request_lines_ids = fields.One2many("xe.product.request.line", "pdt_request_id")

    @api.model
    def create(self, values):
        values["name"] = (
            self.env["ir.sequence"].next_by_code("xe.product.req.seq") or "/"
        )
        res = super(ProductRequest, self).create(values)
        return res

    def action_request(self):
        self.state = "request"

    def accept_request(self):
        self.state = "accept_by_manager"

    def action_issue(self):
        if not self.request_lines_ids:
            raise UserError(_("The record has no request lines"))
        for line in self.request_lines_ids:
            if line.issued_qty <= 0:
                raise UserError(_("Please Add a Valid Issue Quantity"))
            if line.qty_available >= line.issued_qty:
                from_loc = self.env.ref("xe_internal_product_request.from_loc").id
                to_loc = self.env.ref("xe_internal_product_request.to_loc").id
                stock_move = self.env["stock.move"].create(
                    {
                        "name": line.product_id.name,
                        "product_id": line.product_id.id,
                        "location_id": from_loc,
                        "location_dest_id": to_loc,
                        "product_uom_qty": line.issued_qty,
                        "product_uom": line.product_id.uom_id.id,
                        "procure_method": "make_to_stock",
                    }
                )
                self.env["stock.move.line"].create(
                    {
                        "move_id": stock_move.id,
                        "location_id": from_loc,
                        "location_dest_id": to_loc,
                        "product_id": line.product_id.id,
                        "date": fields.Datetime.now(),
                        "product_uom_qty": line.issued_qty,
                        "qty_done": line.issued_qty,
                        "product_uom_id": line.product_id.uom_id.id,
                    }
                )
                inventory_id = self.env["stock.quant"].create(
                    {
                        #                     'name': 'INV: %s' % self.user_id.name,
                        "product_id": line.product_id.id,
                        "location_id": from_loc,
                        "quantity": line.product_id.qty_available,
                        "inventory_quantity": line.issued_qty,
                        "inventory_diff_quantity": line.qty_available - line.issued_qty,
                    }
                )
                #                 inventory_id._action_start()
                #                 inventory_id.line_ids[0].product_qty = line.qty_available - line.issued_qty
                #                 inventory_id._action_done()
                line.qty_available = line.product_id.qty_available
                self.state = "issue"
            else:
                raise UserError(
                    _(f"There is no Enough Quantity to Issue {line.product_id.name}")
                )

    def action_return(self):
        for line in self.request_lines_ids:
            to_loc = self.env.ref("xe_internal_product_request.from_loc").id
            from_loc = self.env.ref("xe_internal_product_request.to_loc").id
            stock_move = self.env["stock.move"].create(
                {
                    "name": line.product_id.name,
                    "product_id": line.product_id.id,
                    "location_id": from_loc,
                    "location_dest_id": to_loc,
                    "product_uom_qty": line.issued_qty,
                    "product_uom": line.product_id.uom_id.id,
                    "procure_method": "make_to_stock",
                }
            )
            self.env["stock.move.line"].create(
                {
                    "move_id": stock_move.id,
                    "location_id": from_loc,
                    "location_dest_id": to_loc,
                    "product_id": line.product_id.id,
                    "date": fields.Datetime.now(),
                    "product_uom_qty": line.issued_qty,
                    "qty_done": line.issued_qty,
                    "product_uom_id": line.product_id.uom_id.id,
                }
            )
            inventory_id = self.env["stock.quant"].create(
                {
                    "name": "INV: %s" % self.user_id.name,
                    "product_ids": [(6, 0, [line.product_id.id])],
                }
            )
            inventory_id._action_start()
            inventory_id.line_ids[0].product_qty = line.qty_available + line.issued_qty
            inventory_id._action_done()
            line.qty_available = line.product_id.qty_available
        self.state = "return"

    def action_cancel(self):
        self.state = "cancel"


class ProductRequestLine(models.Model):
    _name = "xe.product.request.line"
    _description = "Product Request Line"

    product_id = fields.Many2one("product.product", string="Product")
    request_qty = fields.Integer("Requested Quantity")
    issued_qty = fields.Integer("Issued Quantity")
    qty_available = fields.Integer("Onhand Quantity")
    pdt_request_id = fields.Many2one("xe.product.request", string="Product Request")
    state = fields.Selection(related="pdt_request_id.state")

    @api.constrains("issued_qty")
    def _check_issued_qty(self):
        for line in self:
            if line.issued_qty > line.request_qty:
                raise UserError(
                    _(
                        f"Issue Quantity is greater than of Request Quantity for {str(line.product_id.name)}"
                    )
                )

    @api.onchange("product_id")
    def _get_onhand_qty(self):
        for line in self:
            line.qty_available = line.product_id.qty_available
