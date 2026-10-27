from odoo import models, api
from odoo.http import request


class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        ids = super(ir_ui_menu, self).search(
            args, offset=0, limit=None, order=order
        )

        user = self.env.user

        # HTTP requests may not exist during installation or background jobs.
        try:
            cids = request.httprequest.cookies.get('cids')
        except (RuntimeError, AttributeError):
            cids = None

        company_id = (
            int(cids.split(',')[0])
            if cids
            else self.env.company.id
        )

        hidden_menu_ids = user.access_management_ids.filtered(
            lambda line: company_id in line.company_ids.ids
        ).mapped('hide_menu_ids.menu_id')

        for menu_id in hidden_menu_ids:
            menu = self.browse(menu_id.id if hasattr(menu_id, 'id') else menu_id)
            if menu in ids:
                ids = ids - menu

        if offset:
            ids = ids[offset:]
        if limit:
            ids = ids[:limit]

        return ids

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ir_ui_menu, self).create(vals_list)
        menu_item_obj = self.env['menu.item']

        for record in res:
            menu_item_obj.create({
                'name': record.display_name,
                'menu_id': record.id,
            })

        return res

    def unlink(self):
        menu_item_obj = self.env['menu.item']

        for record in self:
            menu_item_obj.search([
                ('menu_id', '=', record.id)
            ]).unlink()

        return super(ir_ui_menu, self).unlink()
