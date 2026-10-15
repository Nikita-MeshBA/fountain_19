from odoo import models, fields, api, _
from uuid import getnode as get_mac
# from getmac import get_mac_address as gma


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    allowed_ips = fields.One2many("allowed.ips", "users_ip", string="IP")
    allowed_macs = fields.One2many("allowed.macs", "mac_users_ip", string="MAC")
    current_mac_system = fields.Char(string="Current MAC")

    @api.onchange("allowed_macs")
    def onchange_allowed_macs(self):
        mac = get_mac()
        mac_string = ":".join(("%012X" % mac)[i : i + 2] for i in range(0, 12, 2))
        self.current_mac_system = mac_string


class AllowedIPs(models.Model):
    _name = "allowed.ips"
    _description = "Allowed IPs"

    users_ip = fields.Many2one("res.users", string="IP")
    ip_address = fields.Char(string="Allowed IP")


class AllowedMacs(models.Model):
    _name = "allowed.macs"
    _description = "Allowed MACs"

    mac_users_ip = fields.Many2one("res.users", string="IP")
    macs_address = fields.Char(string="Allowed MACS")
