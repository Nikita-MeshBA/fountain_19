from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    fee_name = fields.Char()
    fee_structu_id = fields.Many2one("xe.fees.structure")
    fee_structu_type = fields.Selection(
        [
            ("academic", "Academic Fees"),
            ("transport", "Transport Fees"),
            ("activity", "Activity Fees"),
            ("boarding", "Boarding Fees"),
            ("optional", "Optional Fees"),
        ],
        default="academic",
    )
    is_transport_fees = fields.Boolean()
    is_academic = fields.Boolean(string="Is Academic Fees")
    is_activity = fields.Boolean(string="Is Activity Fees")
    is_optional = fields.Boolean(string="Is Optional Fees")
    is_boarding = fields.Boolean()

    def _get_line_ids(self):
        record_set = []
        line_ids = self.invoice_line_ids
        ordered_record_set = line_ids.sorted(key=lambda r: r.price_subtotal)
        opening_line = False
        for line in ordered_record_set:
            record_set.append(line)
            if line.product_id.is_opening_blns:
                opening_line = line
        if opening_line:
            record_set.remove(opening_line)
            record_set.insert(0, opening_line)
        inv_values_array_nofeesreceipt = []
        inv_values_array_withfeesreceipt = []
        total_paid_amount = 0
        total_balance = 0
        fee_receipt_objs = []

        for inv_line in record_set:
            name = inv_line.name
            fee_receipt_id = inv_line.receipt_name_id

            if fee_receipt_id:
                fee_receipt_objs.append(inv_line.receipt_name_id)
            price_unit = inv_line.price_unit
            amount = inv_line.price_subtotal
            invoice_total_paid = 0
            line_paid_amount = 0
            balance = 0
            invoice_state = inv_line.move_id and inv_line.move_id.state

            if invoice_state not in ("draft", "cancel"):
                invoice_total_paid = (
                    inv_line.move_id.amount_total - inv_line.move_id.amount_residual
                )

            if invoice_state in ("draft", "cancel"):
                invoice_total_paid = 0
            if (
                total_paid_amount + inv_line.price_subtotal
            ) < invoice_total_paid and invoice_state not in ("draft", "cancel"):
                line_paid_amount = inv_line.price_subtotal
                balance = 0
            elif (
                total_paid_amount + inv_line.price_subtotal
            ) >= invoice_total_paid and invoice_state not in ("draft", "cancel"):
                if invoice_total_paid > 0:
                    line_paid_amount = invoice_total_paid - total_paid_amount
                else:
                    line_paid_amount = 0
                if line_paid_amount < 0:
                    line_paid_amount = 0
                    balance = inv_line.move_id.amount_total - total_paid_amount

                else:
                    balance = inv_line.price_subtotal - line_paid_amount
            elif (
                total_paid_amount + inv_line.price_subtotal
            ) >= invoice_total_paid and invoice_state in ("draft", "cancel"):
                line_paid_amount = 0
                balance = inv_line.price_subtotal
            total_paid_amount = total_paid_amount + line_paid_amount
            total_balance = total_balance + balance
            inv_values_dict = {
                "name": name,
                "quantity": 1,
                "price_unit": price_unit,
                "taxes": "",
                "amount": amount,
                "paidamount": line_paid_amount,
                "balance": balance,
                "receipt_name_id": inv_line.receipt_name_id.name,
            }

            if not fee_receipt_id:
                inv_values_array_nofeesreceipt.append(inv_values_dict)
            else:
                inv_values_dict = {
                    "name": inv_line.name,
                    "quantity": 1,
                    "price_unit": price_unit,
                    "taxes": "",
                    "amount": amount,
                    "paidamount": line_paid_amount,
                    "balance": balance,
                    "receipt_name_id": inv_line.receipt_name_id.name,
                }

                inv_values_array_withfeesreceipt.append(inv_values_dict)
        if inv_values_array_withfeesreceipt:
            inv_values_array_withfeesreceipt = self.get_grouped(
                inv_values_array_withfeesreceipt, fee_receipt_objs
            )
            inv_values_array_withfeesreceipt = [
                dict(t)
                for t in {tuple(d.items()) for d in inv_values_array_withfeesreceipt}
            ]
        final_array = inv_values_array_withfeesreceipt + inv_values_array_nofeesreceipt
        return final_array

    def get_grouped(self, inv_values_array_withfeesreceipt, fee_receipt_objs):
        res = []
        for receipt in fee_receipt_objs:
            name = receipt.name
            price_unit = 0
            amount = 0
            paidamount = 0
            balance = 0
            quantity = 1
            taxes = ""
            for inv_dict in inv_values_array_withfeesreceipt:
                if name == inv_dict["name"]:
                    price_unit = price_unit + inv_dict["price_unit"]
                    amount = amount + inv_dict["amount"]
                    paidamount = paidamount + inv_dict["paidamount"]
                    balance = balance + inv_dict["balance"]

            modified_dict = {
                "name": name,
                "quantity": quantity,
                "price_unit": price_unit,
                "taxes": taxes,
                "amount": amount,
                "paidamount": paidamount,
                "balance": balance,
            }
            res.append(modified_dict)
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # old field
    receipt_name = fields.Many2one("fee.receipt")
    # new field
    receipt_name_id = fields.Many2one("fee.receipt")
