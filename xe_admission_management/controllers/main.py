# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.http as http
import werkzeug
from odoo.http import request


class EnquiryController(http.Controller):
    @http.route("/Admission/Enquiry/view", type="http", auth="calendar")
    def view_enquiry(self, token, id, **kwargs):
        enquiry = (
            request.env["xe.admission.enquiry"]
            .sudo()
            .search([("access_token", "=", token), ("id", "=", int(id))])
        )
        if not enquiry:
            return request.not_found()

        if request.session.uid and request.env["res.users"].browse(
            request.session.uid
        ).user_has_groups("base.group_user"):
            return werkzeug.utils.redirect(
                "/web?db=%s#id=%s&view_type=form&model=xe.admission.enquiry"
                % (request.env.cr.dbname, id)
            )
