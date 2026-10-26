# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StudentAchievers(models.Model):
    _name = "xe.student.achievers"
    _inherit = ["mail.thread"]
    _description = "Student Achievers"
    _rec_name = "course_id"

    course_id = fields.Many2one("xe.course", "Course", tracking=True)
    teacher_id = fields.Many2one(
        "hr.employee",
        domain=[("teach_type", "=", "teaching")],
        string="Teacher",
        tracking=True,
    )
    achieve_date = fields.Date("Date", default=fields.Date.today(), tracking=True)
    achieve_categ_id = fields.Many2one("xe.achieve.category", tracking=True)
    achieve_line_ids = fields.One2many(
        "xe.student.achiever.line", "achieve_id", string="Achievers Lines"
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")], default="draft", tracking=True
    )

    def act_send_students_list(self):
        self.ensure_one()
        template = self.env.ref(
            "xe_discipline_management.email_student_achievers_list_template", False
        )
        compose_form = self.env.ref("mail.email_compose_message_wizard_form", False)
        ctx = dict(
            default_model="xe.student.achievers",
            default_res_ids=[self.id],
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
            force_email=True,
        )
        self.state = "done"
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }


class StudentAchievers(models.Model):
    _name = "xe.student.achiever.line"
    _description = "Student Achievers Line"

    student_id = fields.Many2one("xe.student", "Student")
    remarks = fields.Char()
    achieve_id = fields.Many2one("xe.student.achievers")
    course_id = fields.Many2one("xe.course", related="achieve_id.course_id")
