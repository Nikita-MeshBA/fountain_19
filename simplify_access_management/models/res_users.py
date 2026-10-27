from odoo import fields, models, api, SUPERUSER_ID,_
from odoo.exceptions import UserError, AccessDenied
import logging
_logger = logging.getLogger(__name__)

class res_users(models.Model):
    _inherit = 'res.users'

    access_management_ids = fields.Many2many('access.management', 'access_management_users_rel_ah', 'user_id', 'access_management_id', 'Access Pack')

    # allow_ip_ids = fields.One2many('allow.ip', 'user_id', 'Allow IP')
    
    def write(self, vals):
        res = super(res_users, self).write(vals)
        for access in self.access_management_ids:
            if self.env.company in access.company_ids and access.readonly:
                if self.has_group('base.group_system') or self.has_group('base.group_erp_manager'):
                    raise UserError(_('Admin user can not be set as a read-only..!'))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(res_users, self).create(vals_list)
        for record in self:
            for access in record.access_management_ids:    
                if self.env.company in access.company_ids and access.readonly:
                    if record.has_group('base.group_system') or record.has_group('base.group_erp_manager'):
                        raise UserError(_('Admin user can not be set as a read-only..!'))
        return res


    @api.model
    def _login(self, credential, user_agent_env):
        auth_info = super()._login(credential, user_agent_env)

        access_management_obj = self.env['access.management'].sudo()
        restricted_user = access_management_obj.search([
            ('user_ids', 'in', auth_info['uid']),
            ('disable_login', '=', True),
        ], limit=1)

        if restricted_user:
            _logger.info(
                "Login blocked for login:%s",
                credential.get('login'),
            )
            raise AccessDenied()

        return auth_info
