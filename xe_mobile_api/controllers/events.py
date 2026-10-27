""" Event APIs python file """
# pylint: disable= E0401, R0801, C0116
from datetime import datetime, date, timedelta
from odoo import http
from odoo.http import request


class CalendarEventsApi(http.Controller):
    """Event APIs"""

    @http.route("/v1/web/fetch/calendar-events", type="json", auth="user")
    def channel_recent_message2(self):
        fields = [
            "id",
            "name",
            "start",
            "stop",
            "duration",
            "allday",
            "user_id",
            "alarm_ids",
            "location",
            "videocall_location",
            "categ_ids",
            "description",
            "partner_ids",
            "privacy",
            "show_as",
        ]
        events = request.env["calendar.event"].search_read([], fields)
        return events

    @http.route("/v1/web/update/calendar-events", type="json", auth="user")
    def calender_events(self, event_id, vals):
        event_obj = request.env["calendar.event"].sudo().browse(event_id)
        result = event_obj.write(vals)
        return result

    @http.route("/v1/web/create/calendar-events", type="json", auth="user")
    def calender_events_create(self, vals):
        event_obj = request.env["calendar.event"]
        result = event_obj.create(vals)
        return result

    @http.route("/v1/web/fetch/events", type="json", auth="user")
    def events_details(self):
        fields = [
            "id",
            "name",
            "date_begin",
            "date_end",
            "organizer_id",
            "user_id",
            "company_id",
            "date_tz",
            # "website_url",
        ]
        events = request.env["event.event"].sudo().search_read([], fields)
        return events

    def set_offset_limit(self, kw):
        offset, limit = 0, 0
        if kw.get("offset", False):
            offset = kw.get("offset")
        if kw.get("limit", False):
            limit = kw.get("limit")
        return offset, limit

    @http.route("/event_details", auth="user", type="json")
    def get_events(self, **kw):
        offset, limit = self.set_offset_limit(kw)
        date = datetime.strptime(kw.get("date"), "%Y-%m-%d").date()

        events = (
            request.env["event.event"]
            .sudo()
            .search([("is_published", "=", True)], offset=offset, limit=limit)
            .filtered(lambda l: l.date_begin.date() == date)
        )
        if events:
            event_data = []
            for event in events:
                event_data.append(self.create_event_vals(event))
            return event_data
        if not events:
            return {"error_message": "There is no events for selected date."}

    def create_event_vals(self, event):
        address = ""
        if event.address_id:
            if event.address_id.street:
                address += event.address_id.street

            if event.address_id.street and event.address_id.street2:
                address += ", " + event.address_id.street2
            elif event.address_id.street2:
                address += event.address_id.street2

            if event.address_id.street2 and event.address_id.city:
                address += ", " + event.address_id.city
            elif event.address_id.city:
                address += event.address_id.city

            if event.address_id.city and event.address_id.state_id:
                address += ", " + event.address_id.state_id.name
            elif event.address_id.state_id:
                address += event.address_id.state_id.name

            if event.address_id.state_id and event.address_id.country_id:
                address += ", " + event.address_id.country_id.name
            elif event.address_id.country_id:
                address += event.address_id.country_id.name

            if event.address_id.country_id and event.address_id.zip:
                address += ", " + event.address_id.zip
            elif event.address_id.zip:
                address += event.address_id.zip

        return {
            "id": event.id,
            "name": event.name,
            "date_begin": event.date_begin.strftime("%Y-%m-%d"),
            "date_end": event.date_end.strftime("%Y-%m-%d"),
            "date_tz": event.date_tz,
            "organizer_id": event.organizer_id
            and [event.organizer_id.id, event.organizer_id.name]
            or False,
            "address": address,
        }

    @http.route("/event/button/website", auth="user", type="json")
    def get_event_website(self, **kw):
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        event_id = request.env["event.event"].sudo().browse([kw.get("event_id")])
        if event_id.website_url:
            return {"website": base_url + event_id.website_url}
        if not event_id.website_url:
            return {"error_message": "No website added in event"}

    @http.route("/events/search", auth="user", type="json")
    def get_event_search(self, **kw):
        offset, limit = self.set_offset_limit(kw)

        event_ids = (
            request.env["event.event"]
            .sudo()
            .search([("name", "ilike", kw.get("searchby"))], offset=offset, limit=limit)
        )

        if kw.get("date"):
            date = datetime.strptime(kw.get("date"), "%Y-%m-%d").date()
            event_ids = event_ids and event_ids.filtered(
                lambda l: l.date_begin.date() == date
            )

        if event_ids:
            event_data = []
            for event in event_ids:
                event_data.append(self.create_event_vals(event))
            return event_data
        if not event_ids:
            return {
                "error_message": "There are no events associated with the search criteria entered."
            }

    @http.route("/events/filter", auth="user", type="json")
    def get_event_filter(self, **kw):
        offset, limit = self.set_offset_limit(kw)

        event_ids = (
            request.env["event.event"].sudo().search([], offset=offset, limit=limit)
        )

        current_date = date.today()
        if kw.get("filterby") == "upcoming_events":
            event_ids = event_ids and event_ids.filtered(
                lambda l: l.date_begin.date() >= current_date
            )
        if kw.get("filterby") == "current_month_events":
            year = current_date.year
            month = current_date.month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year, month, 31)
            else:
                end_date = date(year, month + 1, 1) + timedelta(days=-1)

            event_ids = event_ids and event_ids.filtered(
                lambda l: start_date <= l.date_begin.date() <= end_date
            )

        if kw.get("filterby") == "past_events":
            event_ids = event_ids and event_ids.filtered(
                lambda l: l.date_begin.date() <= current_date
            )

        if event_ids:
            event_data = []
            for event in event_ids:
                event_data.append(self.create_event_vals(event))
            return event_data
        if not event_ids:
            return {
                "error_message": "There are no events associated with the filter criteria."
            }
