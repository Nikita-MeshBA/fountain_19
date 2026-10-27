""" Classroom APIs python file """
# pylint: disable= E0401, C0116
from odoo import http
from odoo.http import request


class XeClassroomApi(http.Controller):
    """Classroom APIs"""

    @http.route("/v1/web/fetch/class-rooms", type="json", auth="user")
    def get_classrooms(self, course_id):
        fields = ["name", "code", "course_id", "capacity"]
        classrooms = []
        classrooms = request.env["xe.classroom"].search_read(
            [("course_id", "=", course_id)], fields
        )
        return classrooms

    @http.route(
        "/v1/web/dataset/fetch/students/class/classroom/base", type="json", auth="user"
    )
    def fetch_students(self, args):
        if "classroom_id" in args:
            student_ids = (
                request.env["xe.student"]
                .sudo()
                .search_read(
                    [
                        ("course_id", "=", int(args["class_id"])),
                        ("classroom_id", "=", int(args["classroom_id"])),
                    ],
                    ["id", "name", "email", "roll_number"],
                )
            )
        else:
            student_ids = (
                request.env["xe.student"]
                .sudo()
                .search_read(
                    [("course_id", "=", int(args["class_id"]))],
                    ["id", "name", "email", "roll_number"],
                )
            )
        return {"student_ids": student_ids}
