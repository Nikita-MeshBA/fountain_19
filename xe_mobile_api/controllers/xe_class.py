""" Class APIs python files """
# pylint: disable= E0401, R0903, C0116
from odoo import http
from odoo.http import request


class XeClassApi(http.Controller):
    """Class APIs"""

    @http.route("/v1/web/dataset/fetch/class", type="json", auth="user")
    def fetch_class(self):
        classes = request.env["xe.course"].sudo().search_read([])
        return {"class": classes}
