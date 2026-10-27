""" Fleet APIs python file """
# pylint: disable= E0401, R0801, C0116
from datetime import datetime
from odoo import http
from odoo.http import request


class FleetVehicleApi(http.Controller):
    """Fleet APIs"""

    @http.route("/v1/web/fetch/vehicle/invoices", type="json", auth="user")
    def get_vehicle_invoices(self, vehicle_id):
        vehicle_cost_objs = request.env["fleet.vehicle.cost"].search(
            [("vehicle_id", "=", vehicle_id)]
        )
        invoices_list = []
        if vehicle_cost_objs:
            invoices = vehicle_cost_objs.mapped("invoice_id")
            for inv in invoices:
                invoices_lines = request.env["account.invoice.line"].search_read(
                    [("id", "in", inv.invoice_line_ids.ids)],
                    [
                        "id",
                        "product_id",
                        "name",
                        "account_id",
                        "account_analytic_id",
                        "quantity",
                        "uom_id",
                        "price_unit",
                        "fixed_discount",
                        "invoice_line_tax_ids",
                        "price_subtotal",
                    ],
                )
                inv_res = inv.read(
                    [
                        "id",
                        "number",
                        "partner_id",
                        "date_due",
                        "origin",
                        "amount_total_signed",
                        "state",
                        "gr_number",
                        "date_invoice",
                        "mpesa_paybill",
                        "payment_tearm_id",
                        "user_id",
                        "team_id",
                        "journal_id",
                        "account_id",
                        "amount_untaxed",
                        "amount_tax",
                        "amount_total",
                    ]
                )[0]
                inv_res["invoices_lines"] = invoices_lines
                invoices_list.append(inv_res)
        return invoices_list

    def set_offset_limit(self, kw):
        offset, limit = 0, 0
        if kw.get("offset", False):
            offset = kw.get("offset")
        if kw.get("limit", False):
            limit = kw.get("limit")
        return offset, limit

    @http.route("/fleet/user/access_rights", type="json", auth="user")
    def get_user_access_rights(self, **kw):
        user = request.env["res.users"].browse(kw.get("user_id"))
        access_right = user.has_group("fleet.fleet_group_manager") or user.has_group(
            "fleet.fleet_group_user"
        )
        return access_right

    @http.route("/fleet/service_type", type="json", auth="user")
    def get_fleet_service_type(self, **kw):
        offset, limit = self.set_offset_limit(kw)
        service_type_ids = request.env["fleet.service.type"].search_read(
            [], ["name"], offset=offset, limit=limit, order="id ASC"
        )
        return service_type_ids

    @http.route("/fleet/vendors", type="json", auth="user")
    def get_vendors(self, **kw):
        offset, limit = self.set_offset_limit(kw)
        partner_ids = request.env["res.partner"].search_read(
            [], ["name"], offset=offset, limit=limit, order="id ASC"
        )
        return partner_ids

    @http.route("/fleet/vehicles", type="json", auth="user")
    def get_vehicles(self, **kw):
        offset, limit = self.set_offset_limit(kw)
        vehicle_ids = request.env["fleet.vehicle"].search_read(
            [], ["name"], offset=offset, limit=limit, order="id ASC"
        )
        return vehicle_ids

    @http.route("/fleet/services", type="json", auth="user")
    def get_services(self, **kw):
        offset, limit = self.set_offset_limit(kw)
        date = datetime.strptime(kw.get("date"), "%Y-%m-%d").date()
        service_ids = request.env["fleet.vehicle.log.services"].search_read(
            [("date", "=", date)],
            [
                "description",
                "service_type_id",
                "date",
                "amount",
                "vendor_id",
                "vehicle_id",
                "purchaser_id",
                "odometer",
                "notes",
            ],
            offset=offset,
            limit=limit,
            order="id ASC",
        )
        if service_ids:
            return service_ids
        if not service_ids:
            return {
                "error_message": "There is no services available for selected date."
            }

    @http.route("/fleet/service/create", type="json", auth="user")
    def create_service(self, **kw):
        service_type_id = kw.get("service_type_id", False)
        if not service_type_id:
            return {"error_message": "Service type mandatory."}

        vehicle_id = kw.get("vehicle_id", False)
        if not vehicle_id:
            return {"error_message": "Vehicle Id mandatory."}

        vals = {
            "description": kw.get("description", None),
            "service_type_id": service_type_id,
            "date": kw.get("date", False),
            "amount": kw.get("amount", False),
            "vendor_id": kw.get("vendor_id", False),
            "vehicle_id": vehicle_id,
            "purchaser_id": kw.get("purchaser_id", False),
            "odometer": kw.get("odometer", False),
            "notes": kw.get("notes", False),
        }
        try:
            service = request.env["fleet.vehicle.log.services"].sudo().create(vals)
        except:
            return {"error_message": "Service not created."}
        return True

    @http.route("/fleet/service/write", type="json", auth="user")
    def update_service(self, **kw):
        vals = {}
        service_id = kw.get("service_id", False)
        if not service_id:
            return {"error_message": "Service Id required."}

        if kw.get("description", False):
            vals["description"] = kw.get("description")

        if kw.get("service_type_id", False):
            vals["service_type_id"] = kw.get("service_type_id")

        if kw.get("date", False):
            vals["date"] = kw.get("date")

        if kw.get("amount", False):
            vals["amount"] = kw.get("amount")

        if kw.get("vendor_id", False):
            vals["vendor_id"] = kw.get("vendor_id")

        if kw.get("vehicle_id", False):
            vals["vehicle_id"] = kw.get("vehicle_id")

        if kw.get("purchaser_id", False):
            vals["purchaser_id"] = kw.get("purchaser_id")

        if kw.get("odometer", False):
            vals["odometer"] = kw.get("odometer")

        if kw.get("notes", False):
            vals["notes"] = kw.get("notes")

        service_id = (
            request.env["fleet.vehicle.log.services"]
            .sudo()
            .browse(kw.get("service_id"))
            .write(vals)
        )
        return True

    @http.route("/fleet/service/update_state", type="json", auth="user")
    def service_update_state(self, **kw):
        service_id = (
            request.env["fleet.vehicle.log.services"]
            .sudo()
            .browse(kw.get("service_id"))
        )
        try:
            service_id.state = kw.get("state")
            return True
        except Exception as e:
            return {"error_message": e}

    @http.route("/fleet/odometer/create", type="json", auth="user")
    def create_odometer(self, **kw):
        vehicle_id = kw.get("vehicle_id", False)
        if not vehicle_id:
            return {"error_message": "Vehicle Id mandatory."}

        vals = {
            "vehicle_id": vehicle_id,
            "date": kw.get("date", False),
            "value": kw.get("value", False),
            "driver_id": kw.get("driver_id", False),
        }
        try:
            odometer = request.env["fleet.vehicle.odometer"].sudo().create(vals)
        except:
            return {"error_message": "Odometer not created."}
        return True

    @http.route("/fleet/odometers", type="json", auth="user")
    def get_odometers(self, **kw):
        offset, limit = self.set_offset_limit(kw)
        odometer_ids = (
            request.env["fleet.vehicle.odometer"]
            .sudo()
            .search_read(
                [],
                ["name", "date", "value", "vehicle_id", "driver_id"],
                offset=offset,
                limit=limit,
                order="id ASC",
            )
        )
        if odometer_ids:
            return odometer_ids
        if not odometer_ids:
            return {"error_message": "There is no odometer available."}
