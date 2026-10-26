from odoo import models, fields


class GenerateMedia(models.TransientModel):
    _name = "generate.media.units"
    _description = "Generate Media Units"

    media_id = fields.Many2one("xe.media")
    no_of_units = fields.Integer("Number of Units")

    def generate_media_units(self):
        no_of_units = self.no_of_units
        count = 0
        media_unit_obj = self.env["xe.media.unit"]
        vals = {"media_id": self.media_id.id}
        while count < no_of_units:
            media_unit_obj.create(vals)
            count += 1
        return True
