from odoo import fields, models


class TransportationReportWizard(models.TransientModel):
    _name = "xe.transport.report.wizard"
    _description = "Transport Information Report Wizard"

    route_ids = fields.Many2many("xe.route", string="Route")

    def print_report_pdf(self):
        data = {}
        data["form"] = self.read(["route_ids"])[0]
        return (
            self.env.ref("xe_transportation_management.action_report_transport_details")
            .with_context(landscape=False)
            .report_action(self, data=data)
        )

    def print_report_excel(self):
        data = {
            "ids": self.route_ids.ids,
            "model": "xe.route",
            "form": self.read(["route_ids"])[0],
        }
        return self.env.ref(
            "xe_transportation_management.transport_xlsx_report"
        ).report_action(self, data=data)
