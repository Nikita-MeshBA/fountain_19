from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    gratuity_period = fields.Integer()
    nssf_no = fields.Char("NSSF No")
    nhif_no = fields.Char("NHIF No")
    helb_no = fields.Char("HELB No")
    employee_id_gen_method = fields.Selection(
        selection=[
            ("random", "Random"),
            ("sequence", "Sequence"),
        ],
        string="Generation Method",
        default="random",
    )
    employee_id_random_digits = fields.Integer(
        string="# of Digits", default=5, help="Number of digits in employee identifier"
    )
    # old field
    employee_id_sequence = fields.Many2one(
        comodel_name="ir.sequence",
        string="Identifier Sequence",
        help="Pattern to be used for employee identifier generation",
    )
    # new field
    employee_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Identifier Sequence",
        help="Pattern to be used for employee identifier generation",
    )

    employee_id_front_end = fields.Boolean()
    employee_id_back_end = fields.Boolean()
    type_select = fields.Selection(
        selection=[
            ("front", "Front Side"),
            ("back", "Back Side"),
            ("both", "Both"),
        ],
        string="Employee Template",
        default="both",
    )
    # old field
    employee_front_side = fields.Many2one(
        "ir.ui.view", domain="[('name','=','employee_front_side_report')]"
    )
    # new field
    employee_front_side_id = fields.Many2one(
        "ir.ui.view", domain="[('name','=','employee_front_side_report')]"
    )
    # old field
    employee_back_side = fields.Many2one(
        "ir.ui.view", domain="[('name','=','employee_back_side_report')]"
    )
    # new field
    employee_back_side_id = fields.Many2one(
        "ir.ui.view", domain="[('name','=','employee_back_side_report')]"
    )
    type_select_std = fields.Selection(
        selection=[
            ("front", "Front Side"),
            ("back", "Back Side"),
            ("both", "Both"),
        ],
        string="Student Template",
        default="both",
    )
    # old field
    student_front_side = fields.Many2one(
        "ir.ui.view", domain="[('name','=','stud_front_side_report')]"
    )
    # new field
    student_front_side_id = fields.Many2one(
        "ir.ui.view", domain="[('name','=','stud_front_side_report')]"
    )
    # old field
    student_back_side = fields.Many2one(
        "ir.ui.view", domain="[('name','=','stud_back_side_report')]"
    )
    # new field
    student_back_side_id = fields.Many2one(
        "ir.ui.view", domain="[('name','=','stud_back_side_report')]"
    )
    signature = fields.Binary()


class ResBank(models.Model):
    _inherit = "res.bank"

    swift_code = fields.Char()
