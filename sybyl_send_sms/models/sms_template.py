import dateutil.relativedelta as relativedelta
import functools
import logging
from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from werkzeug import urls

_logger = logging.getLogger(__name__)

try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment

    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,  # do not output newline after blocks
        autoescape=True,  # XML/HTML automatic escaping
    )
    mako_template_env.globals.update(
        {
            "str": str,
            "quote": urls.url_quote,
            "urlencode": urls.url_encode,
            "datetime": datetime,
            "len": len,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "filter": filter,
            "reduce": functools.reduce,
            "map": map,
            "round": round,
            # dateutil.relativedelta is an old-style class and cannot be directly
            # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
            # is needed, apparently.
            "relativedelta": lambda *a, **kw: relativedelta.relativedelta(*a, **kw),
        }
    )
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class SmsTemplate(models.Model):
    _name = "send.sms.template"
    _description = "send SMS Template"

    def _default_gateway_account(self):
        account_id = self.env["sms.gateway"].search([("active", "=", True)], limit=1).id
        return account_id

    name = fields.Char(required=True, string="Template Name")
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Applies to",
        help="The kind of document with with this template can be used",
    )
    model = fields.Char(
        related="model_id.model",
        store=True,
        readonly=True,
        string="Related Document Model",
        index=True,
    )
    template_body = fields.Text("Body", translate=True, help="Plain text of message")
    msg_to = fields.Char(string="To Mobile")
    # old field
    sms_account_gateway = fields.Many2one(
        "sms.gateway",
        string="Account",
        default=_default_gateway_account,
        domain=[("active", "=", True)],
    )
    # new field
    sms_account_gateway_id = fields.Many2one(
        "sms.gateway",
        string="Account",
        default=_default_gateway_account,
        domain=[("active", "=", True)],
    )
    # old field
    model_object_field = fields.Many2one("ir.model.fields", string="Field")
    # new field
    model_object_field_id = fields.Many2one("ir.model.fields", string="Field")
    sub_object_id = fields.Many2one("ir.model", string="Sub-model", readonly=True)
    # old field
    sub_model_object_field = fields.Many2one("ir.model.fields", string="Sub-field")
    # new field
    sub_model_object_field_id = fields.Many2one("ir.model.fields", string="Sub-field")
    null_value = fields.Char(
        string="Default Value",
        help="Optional value to use if the target field is empty",
    )
    copyvalue = fields.Char(
        string="Placeholder Expression",
        help="Final placeholder expression, to be "
        "copy-pasted in the desired template field.",
    )
    lang = fields.Char(string="Language", placeholder="${object.partner_id.lang}")

    @api.onchange("model_object_field_id")
    def _onchange_model_object_field_id(self):
        if self.model_object_field_id.relation:
            self.sub_object_id = (
                self.env["ir.model"]
                .search([("model", "=", self.model_object_field_id.relation)], limit=1)
                .id
            )
        else:
            self.sub_object_id = False
        if self.model_object_field_id:
            self.copyvalue = self.build_expression(
                self.model_object_field_id.name,
                self.sub_model_object_field_id.name,
                self.null_value,
            )

    @api.onchange("sub_model_object_field_id")
    def _onchange_sub_model_object_field_id(self):
        if self.sub_model_object_field_id:
            self.copyvalue = self.build_expression(
                self.model_object_field_id.name,
                self.sub_model_object_field_id.name,
                self.null_value,
            )

    @api.model
    def send_sms(self, template_id, record_id):
        """Send sms"""
        send_sms_template = self.env["send.sms.template"]
        template = send_sms_template.browse(int(template_id))
        if not template.active:
            return True
        sms_rendered_content = send_sms_template.render_template(
            template.template_body, template.model_id.model, record_id
        )
        rendered_msg_to = send_sms_template.render_template(
            template.msg_to, template.model_id.model, record_id
        )
        gateway_model = template.sms_account_gateway_id
        if gateway_model:
            gateway_model.send_sms(
                rendered_msg_to,
                sms_rendered_content,
                template.model_id.model,
                record_id,
                template_id,
            )
        else:
            raise UserError(_("Gateway not defined in SMS Template"))

    def render_template(self, template, model, res_id):
        """Render the given template text, replace mako expressions ``${expr}``
        with the result of evaluating these expressions with
        an evaluation context containing:

             * ``user``: browse_record of the current user
             * ``object``: browse_record of the document record this mail is
                           related to
             * ``context``: the context passed to the mail composition
             wizard

        :param str template: the template text to render
        :param str model: model name of the document record this mail is
        related to.
        :param int res_id: id of document records those mails are related
         to.
        """
        # try to load the template
        template = mako_template_env.from_string(tools.ustr(template))
        # prepare template variables
        user = self.env.user
        record = self.env[model].browse(res_id)
        variables = {"user": user, "object": record}
        try:
            render_result = template.render(variables)
        except Exception:
            _logger.error(
                "Failed to render template %r using values %r" % (template, variables)
            )
            render_result = ""
        if render_result == "False":
            render_result = ""
        return render_result

    @api.model
    def build_expression(self, field_name, sub_field_name, null_value):
        """Returns a placeholder expression for use in a template field,
         based on the values provided in the placeholder assistant.

        :param field_name: main field name
        :param sub_field_name: sub field name (M2O)
        :param null_value: default value if the target value is empty
        :return: final placeholder expression
        """
        expression = ""
        if field_name:
            expression = "${object." + field_name
            if sub_field_name:
                expression += "." + sub_field_name
            if null_value:
                expression += " or '''%s'''" % null_value
            expression += "}"
        return expression
