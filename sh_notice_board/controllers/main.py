# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from datetime import datetime

from odoo.http import request, Response
from odoo.osv import expression
from odoo.tools import json

from odoo import http


class Main(http.Controller):
    @http.route("/get_latest_news", auth="public", website=True)
    def get_latest_news(self, limit=False):
        domain = [("active", "=", True), ("is_published", "=", True)]
        domain = expression.AND(
            [
                domain,
                [
                    "|",
                    ("website_id", "=", request.website.id),
                    ("website_id", "=", False),
                ],
            ]
        )

        if limit and limit.isdigit():
            limit = int(limit)
            latest_news_records = (
                request.env["sh.nb.notice.board"]
                .sudo()
                .search_read(domain, limit=limit, order="sequence asc")
            )
        else:
            latest_news_records = (
                request.env["sh.nb.notice.board"]
                .sudo()
                .search_read(domain, order="sequence asc")
            )
        # Convert datetime objects to string representations
        for record in latest_news_records:
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = value.strftime("%Y-%m-%d %H:%M:%S")

        # Serialize the records to JSON and return an HttpResponse
        return Response(
            json.dumps(latest_news_records), content_type="application/json"
        )
