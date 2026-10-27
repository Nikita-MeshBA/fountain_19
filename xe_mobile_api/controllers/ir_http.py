""" Seesion APIs python file """
# pylint: disable= E0401, C0116, R0903, R0801
from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    """Ir HTTP class inherit"""

    _inherit = "ir.http"

    def session_info(self):
        res = super(Http, self).session_info()
        school_access_role = ""
        is_student = self.env.user.has_group("xenesis_school_base.group_xe_student")
        is_teacher = self.env.user.has_group("xenesis_school_base.group_xe_staff")
        is_parent = self.env.user.has_group("xenesis_school_base.group_xe_parent")
        is_back_office_admin = self.env.user.has_group(
            "xenesis_school_base.group_xe_admin"
        )
        if is_student:
            school_access_role = "student"
        if is_parent:
            school_access_role = "parent"
        if is_teacher:
            school_access_role = "teacher"
        if is_back_office_admin:
            school_access_role = "back_office_admin"
        res["school_access"] = school_access_role

        # Old Code
        # employee_obj = (
        #     request.env["hr.employee"]
        #     .sudo()
        #     .search([("user_id", "=", self.env.user.id)])
        # )

        # New Code
        employee_obj = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", request.env.user.id)], limit=1)
        )
        
        if employee_obj:
            res["employee_id"] = employee_obj.id
        if school_access_role == "teacher":
            teacher_id = request.env["xe.staff"].search(
                [("partner_id", "=", self.env.user.partner_id.id)]
            )
            res["teacher_id"] = teacher_id.id
        elif school_access_role == "student":
            student_id = request.env["xe.student"].search(
                [("partner_id", "=", self.env.user.partner_id.id)]
            )
            res["student_id"] = student_id.id
        elif school_access_role == "parent":
            parent_id = request.env["xe.parent"].search(
                [("user_id", "=", self.env.user.id)]
            )
            student_ids = parent_id.sudo().student_ids
            if student_ids:
                student_list = []
                for student in student_ids:
                    s_info = student.read(["id", "name", "roll_number", "email"])[0]
                    student_list.append(s_info)
                res["student_ids"] = student_list
                res["parent_id"] = parent_id.id
        res["version"] = 17
        return res
