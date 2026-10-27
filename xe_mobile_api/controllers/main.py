""" Application APIs python file """
# pylint: disable= E0401, C0116
import base64
import json
import logging
import calendar
from odoo import http, _, SUPERUSER_ID
from odoo.http import request
# from odoo.addons.web.controllers.main import DataSet
from odoo.service.model import call_kw
from odoo.exceptions import AccessError, MissingError
from odoo.tools import consteq

_logger = logging.getLogger(__name__)


def set_offset_limit(kw):
    offset, limit = 0, 0
    if kw.get("offset", False):
        offset = kw.get("offset")
    if kw.get("limit", False):
        limit = kw.get("limit")
    return offset, limit

class ApplicationApi(http.Controller):
    """Application APIs python file"""

    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.sudo(SUPERUSER_ID)
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        try:
            document.check_access_rights("read")
            document.check_access_rule("read")
        except AccessError:
            if (
                not access_token
                or not document_sudo.access_token
                or not consteq(document_sudo.access_token, access_token)
            ):
                raise
        return document_sudo

    @http.route("/app/privacy", type="http", auth="public", website=True, csrf=False)
    def get_privacy_policy(self):
        return "https://sybyl.com/privacypolicy/"

    @http.route(
        "/v1/web/dataset/upload/attachment", methods=["POST"], csrf=False, auth="user"
    )
    def upload_file(self, file, res_model, res_id):
        ir_attachment = request.env["ir.attachment"]
        attachment = ir_attachment.sudo().create(
            {
                "name": file.filename,
                "datas": base64.b64encode(file.read()),
                "res_model": res_model,
                "res_id": res_id,
            }
        )
        _logger.info(attachment)
        return request.make_response(
            data=json.dumps(
                attachment.read(
                    ["id", "name", "mimetype", "file_size", "access_token"]
                )[0]
            ),
            headers=[("Content-Type", "application/json")],
        )

    @http.route("/v1/web/dataset/push/notification/token", type="json", auth="user")
    def write_partner_token(self, partner_id, token):
        partners = (
            request.env["res.partner"].sudo().search([("firebase_token", "=", token)])
        )
        if partners:
            partners.sudo().write({"firebase_token": ""})
        partner = request.env["res.partner"].sudo().browse(partner_id)
        if partner:
            partner.sudo().write({"firebase_token": token})
        return True

    @http.route("/v1/web/dataset/remove/notification/token", type="json", auth="user")
    def remove_partner_token(self, partner_id, token):
        partners = (
            request.env["res.partner"].sudo().search([("firebase_token", "=", token)])
        )
        if partners:
            partners.sudo().write({"firebase_token": ""})
        partner = request.env["res.partner"].sudo().browse(partner_id)
        if partner:
            partner.sudo().write({"firebase_token": ""})
        return True

    def get_salary_collections(self, year):
        # Compute days wise expense
        j_query = """SELECT SUM(aml.total) FROM hr_payslip AS ac
                    JOIN hr_payslip_line AS aml on aml.slip_id = ac.id
                    WHERE ac.state IN ('done')AND 
                    EXTRACT(YEAR FROM ac.date_to) = %s
                    """
        request.cr.execute(j_query, (year,))
        result = request.cr.fetchone()[0]
        return result

    @http.route("/salary/collection/year", type="json", auth="user")
    def _get_salary_collection_yearly(self, year):
        salary_list = []
        salary_dict = {
            1: 00,
            2: 00,
            3: 00,
            4: 00,
            5: 00,
            6: 00,
            7: 00,
            8: 00,
            9: 00,
            10: 00,
            11: 00,
            12: 00,
        }

        # Compute month wise salary
        j_query = """SELECT EXTRACT(YEAR FROM ac.date_to) AS year, EXTRACT(MONTH From ac.date_to)
                        AS month ,SUM(aml.total) FROM hr_payslip AS ac JOIN hr_payslip_line AS aml on aml.slip_id = ac.id
                        WHERE ac.state IN ('done')AND aml.code = 'NET' AND
                        EXTRACT(YEAR FROM ac.date_to) = %s
                        GROUP BY year,month order by year, month """
        request.cr.execute(j_query, (year,))
        result = request.cr.fetchall()
        total_amt = 0
        for line in result:
            salary_dict[int(line[1])] += line[2]
            total_amt += line[2]
        for key, value in salary_dict.items():
            percentage = 0
            if total_amt:
                percentage = (value / total_amt) * 100

            new_dict = {
                "month_code": key,
                "month_name": calendar.month_name[key],
                "amount": value,
                "percentage": percentage,
            }
            salary_list.append(new_dict)
        return {
            "salary_list": salary_list,
        }

    @http.route("/v1/web/income/collection/year", type="json", auth="user")
    def _get_income_collection_yearly(self, year):
        fees_list = []
        fees_dict = {
            1: 00,
            2: 00,
            3: 00,
            4: 00,
            5: 00,
            6: 00,
            7: 00,
            8: 00,
            9: 00,
            10: 00,
            11: 00,
            12: 00,
        }

        # Compute days wise expense
        j_query = """SELECT EXTRACT(YEAR FROM ac.payment_date) AS year, \
                        EXTRACT(MONTH From ac.payment_date)
                        AS month ,SUM(aml.amount_residual),ac.payment_type FROM \
                        account_payment AS ac JOIN account_move_line AS \
                        aml on aml.payment_id = ac.id
                        LEFT JOIN account_journal as aj ON aj.id = ac.journal_id
                        WHERE ac.state IN ('posted', 'reconciled')AND 
                        EXTRACT(YEAR FROM ac.payment_date) = %s GROUP BY \
                        year,month,ac.payment_type order by year, month,ac.payment_type """
        request.cr.execute(j_query, (year,))
        result = request.cr.fetchall()
        total_fees = 0
        for line in result:
            if line[3] == "inbound":
                fees_dict[int(line[1])] += line[2]
                total_fees += line[2]
        for key, value in fees_dict.items():
            percentage = 0
            if total_fees:
                percentage = (value / total_fees) * 100

            new_dict = {
                "month_code": key,
                "month_name": calendar.month_name[key],
                "amount": value,
                "percentage": percentage,
            }
            fees_list.append(new_dict)

        return {
            "income_yearly_list": fees_list,
        }

    @http.route("/v1/web/dataset/fetch/messages", type="json", auth="user")
    def fetch_message_by_channel(self, channel_id, partner_id, limit=1000):
        channel_obj = request.env["discuss.channel"]
        channel = channel_obj.browse(channel_id)
        result = []
        if channel:
            result = channel.get_last_channel_fetch_message(partner_id, limit)
        return result

    @http.route("/v1/web/dataset/message/post", type="json", auth="user")
    def message_post_api(self, model, method, args, kwargs):
        result = DataSet()._call_kw(model, method, args, kwargs=kwargs)
        if isinstance(result, int):
            res = request.env["mail.message"].browse(result).read([])
            for attachment in res:
                if attachment.get("attachment_ids"):
                    attachments = request.env["ir.attachment"].search_read(
                        [("id", "in", attachment["attachment_ids"])],
                        ["id", "mimetype", "name", "file_size"],
                    )
                    if attachments:
                        attachment["attachment_ids"] = attachments
            return res
        return result

    @http.route("/v1/web/fetch/timetable", type="json", auth="user")
    def get_time_tables(self, uid, user_type=""):
        timetables = []
        fields = [
            "id",
            "name",
            "start_time",
            "end_time",
            "duration",
            "day",
            "session_date",
            "course_id",
            "teacher_id",
            "term_id",
            "subject_id",
            "class_room_id",
            "academic_term_id",
        ]
        sessions = request.env["xe.session.lines"].sudo()
        if user_type == "":
            return timetables
        if user_type in ["parent", "student"]:
            student = request.env["xe.student"].sudo().browse(uid)
            for res in student:
                mandatory_subject = res.mandatory_subjects_ids.ids
                elective_subjects_ids = res.elective_subjects_ids.ids
                subjects = mandatory_subject + elective_subjects_ids
                domain = [("course_id", "=", res.course_id.id)]
                if res.classroom_id:
                    domain.append(("class_room_id", "=", res.classroom_id.id))
                if subjects:
                    domain.append(("subject_id", "=", subjects))
                timetables = sessions.sudo().search_read(domain, fields)
        elif user_type == "faculty":
            timetables = sessions.sudo().search_read([("teacher_id", "=", uid)], fields)
        elif user_type == "admin":
            timetables = sessions.sudo().search_read([], fields)
        return timetables

    @http.route("/v1/web/fetch/channel-messages", type="json", auth="user")
    def channel_message(self, channel_id):
        channel = request.env["discuss.channel"].sudo().browse(channel_id)
        fields = [
            "id",
            "body",
            "description",
            "attachment_ids",
            "author_id",
            "channel_ids",
        ]
        messgaes = (
            request.env["mail.message"]
            .sudo()
            .search_read([("id", "in", channel.message_ids.ids)], fields, limit=50)
        )
        return messgaes

    @http.route("/v1/web/fetch/recent-messages", type="json", auth="user")
    def channel_recent_message(self):
        channels = request.env["discuss.channel"].sudo().search([])
        fields = [
            "id",
            "body",
            "description",
            "attachment_ids",
            "author_id",
            "channel_ids",
        ]
        result_return = []
        for channel in channels:
            author_ids = []
            messgaes = (
                request.env["mail.message"]
                .sudo()
                .search_read(
                    [("id", "in", channel.message_ids.ids)], fields, order="id desc"
                )
            )
            for msg in messgaes:
                if msg["author_id"] not in author_ids:
                    msg["channel_id"] = channel.id
                    result_return.append(msg)
                    author_ids.append(msg["author_id"])
        return result_return

    @http.route("/attachment/delete", type="json", auth="user")
    def delete_attachment(self, **kw):
        pdfhttpheaders = [
            ("Content-Type", "application/json"),
        ]
        result_dict = {}
        try:
            attachment = (
                request.env["ir.attachment"]
                .sudo()
                .search([("id", "=", kw.get("attachment_id"))])
            )
            attachment.unlink()
            result_dict = {"status": "Attachment deleted."}
        except Exception as e:
            result_dict = {"status": "Failed", "flag": False, "error": str(e)}
        return result_dict
