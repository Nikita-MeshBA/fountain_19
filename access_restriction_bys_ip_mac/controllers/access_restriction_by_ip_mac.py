import odoo.modules.registry
import werkzeug.datastructures
import werkzeug.exceptions
import werkzeug.local
import werkzeug.routing
import werkzeug.wrappers
from odoo.http import request
from odoo.tools.translate import _

import odoo
from odoo import http
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import ensure_db

try:
    from werkzeug.middleware.shared_data import SharedDataMiddleware
except ImportError:
    from werkzeug.wsgi import SharedDataMiddleware


def redirect_with_hash(url, code=303):
    # Section 7.1.2 of RFC 7231 requires preservation of URL fragment through redirects,
    # so we don't need any special handling anymore. This function could be dropped in the future.
    # seealso : http://www.rfc-editor.org/info/rfc7231
    #           https://tools.ietf.org/html/rfc7231#section-7.1.2
    return werkzeug.utils.redirect(url, code)


class AccessHome(Home):
    @http.route("/web/login", type="http", auth="public")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params["login_success"] = False
        if request.httprequest.method == "GET" and redirect and request.session.uid:
            return redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values["databases"] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values["databases"] = None
        if request.httprequest.method == "POST":
            old_uid = request.uid
            ip_address = request.httprequest.environ["REMOTE_ADDR"]
            if request.params["login"]:
                user_rec = (
                    request.env["res.users"]
                    .sudo()
                    .search([("login", "=", request.params["login"])])
                )
                if user_rec.allowed_ips:
                    ip_list = []
                    for rec in user_rec.allowed_ips:
                        ip_list.append(rec.ip_address)
                    if ip_address in ip_list:
                        try:
                            # uid = request.session.authenticate(
                            #     request.session.db,
                            #     request.params["login"],
                            #     request.params["password"],
                            # )
                            auth_info = request.session.authenticate(                                request.env,
                                {
                                    "login": request.params["login"],
                                    "password": request.params["password"],
                                    "type": "password",
                                },
                            )
                            request.params["login_success"] = True
                            return redirect_with_hash(
                                self._login_redirect(uid, redirect=redirect)
                            )
                        except odoo.exceptions.AccessDenied as e:
                            request.uid = old_uid
                            if e.args == odoo.exceptions.AccessDenied().args:
                                values["error"] = _("Wrong login/password")
                    else:
                        request.uid = old_uid
                        values["error"] = _("Not allowed to login from this IP")
                # else:
                #     try:
                #         uid = request.session.authenticate(request.session.db,
                #                                            request.params['login'],
                #                                            request.params['password'])
                #         request.params['login_success'] = True
                #         return redirect_with_hash(self._login_redirect(uid, redirect=redirect))
                #     except odoo.exceptions.AccessDenied as e:
                #         request.uid = old_uid
                #         if e.args == odoo.exceptions.AccessDenied().args:
                #             values['error'] = _("Wrong login/password")
                elif user_rec.allowed_macs:
                    mac_list = []
                    # now_mac = str(uuid.getnode())
                    # from getmac import get_mac_address as gma
                    from uuid import getnode as get_mac

                    # now_mac = str(gma())
                    mac = get_mac()
                    now_mac = ":".join(
                        ("%012X" % mac)[i : i + 2] for i in range(0, 12, 2)
                    )
                    # now_mac = '5645654654654'
                    # for rec in user_rec.allowed_macs.filtered(lambda a: a.macs_address == str(now_mac)):
                    for rec in user_rec.allowed_macs:
                        mac_list.append(rec.macs_address)
                    if now_mac in mac_list:
                        try:
                            # uid = request.session.authenticate(
                            #     request.session.db,
                            #     request.params["login"],
                            #     request.params["password"],
                            # )
                            auth_info = request.session.authenticate(                                request.env,
                                {
                                    "login": request.params["login"],
                                    "password": request.params["password"],
                                    "type": "password",
                                },
                            )
                            request.params["login_success"] = True
                            return redirect_with_hash(
                                self._login_redirect(uid, redirect=redirect)
                            )
                        except odoo.exceptions.AccessDenied as e:
                            request.uid = old_uid
                            if e.args == odoo.exceptions.AccessDenied().args:
                                values["error"] = _("Wrong login/password")
                    else:
                        # request.uid = old_uid
                        values["error"] = _("Not allowed to login from this MAC")
                else:
                    try:
                        # uid = request.session.authenticate(
                        #     request.session.db,
                        #     request.params["login"],
                        #     request.params["password"],
                        # )
                        auth_info = request.session.authenticate(                            request.env,
                            {
                                "login": request.params["login"],
                                "password": request.params["password"],
                                "type": "password",
                            },
                        )
                        request.params["login_success"] = True
                        return redirect_with_hash(
                            self._login_redirect(uid, redirect=redirect)
                        )
                    except odoo.exceptions.AccessDenied as e:
                        request.uid = old_uid
                        if e.args == odoo.exceptions.AccessDenied().args:
                            values["error"] = _("Wrong login/password")

        return request.render("web.login", values)
