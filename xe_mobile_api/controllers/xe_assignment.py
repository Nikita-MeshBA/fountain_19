""" Assignment APIs python file """
# pylint: disable= E0401, R0801, C0116, W0718, C0209
import io
import json
import base64
from werkzeug.utils import redirect
from odoo import http
from odoo.http import request
from ..controllers.main import set_offset_limit


class XeAssignmentApi(http.Controller):
    """Assignment APIs"""

    def get_user_type(self):
        res = {}
        school_access_role = ""
        is_student = request.env.user.has_group("xenesis_school_base.group_xe_student")
        is_teacher = request.env.user.has_group("xenesis_school_base.group_xe_staff")
        is_parent = request.env.user.has_group("xenesis_school_base.group_xe_parent")
        is_back_office_admin = request.env.user.has_group(
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
        if school_access_role == "teacher":
            teacher_id = request.env["xe.staff"].search(
                [("partner_id", "=", request.env.user.partner_id.id)]
            )
            res["teacher_id"] = teacher_id.id
        elif school_access_role == "student":
            student_id = request.env["xe.student"].search(
                [("partner_id", "=", request.env.user.partner_id.id)]
            )
            res["student_id"] = student_id.id
        elif school_access_role == "parent":
            parent_id = request.env["xe.parent"].search(
                [("user_id", "=", request.env.user.id)]
            )
            res["parent_id"] = parent_id.id
        res["company_id"] = (
            request.env.user.company_id and request.env.user.company_id.id or False
        )
        return res

    @http.route("/v1/web/dataset/assignment/create", type="json", auth="user")
    def create_assignment(self, args):
        if args:
            vals = args[0]
            record = request.env["xe.assignment"].create(vals)
            return {"result": record.id}
        return {"result": False}

    @http.route("/v1/web/dataset/xe/assignment/line", type="json", auth="user")
    def get_assignment_line_by_id(self, assignment_line_id, fields):
        assignment_lines = []
        assignmentline = request.env["xe.assignment.submission"].search_read(
            [("id", "=", assignment_line_id)], fields
        )
        if assignmentline:
            attachments = request.env["ir.attachment"].search_read(
                [
                    ("res_id", "=", assignment_line_id),
                    ("res_model", "=", "xe.assignment.submission"),
                ],
                ["id", "name", "mimetype", "file_size"],
            )
            temp = assignmentline[0]
            temp["attachment_ids"] = attachments
            assignment_lines = [temp]
        return assignment_lines

    @http.route("/v1/web/dataset/fetch/assignment/details", type="json", auth="user")
    def fetch_assignment_details(self, assignment_id):
        fetched_assignment = (
            request.env["xe.assignment"]
            .sudo()
            .search_read([("id", "=", int(assignment_id))])
        )
        if not fetched_assignment:
            return {"assignment_details": [], "fetch_assignment_details": True}
        return {
            "assignment_details": fetched_assignment,
            "student_ids": request.env["xe.student"]
            .sudo()
            .search_read(
                [("id", "in", fetched_assignment[0]["student_ids"])],
                ["id", "name", "roll_number", "email"],
            ),
        }

    @http.route(
        "/v1/web/dataset/fetch/teacher/assignment/details", type="json", auth="user"
    )
    def fetch_user_assignment_details(self, **kw):
        offset, limit = set_offset_limit(kw)
        domain = [("create_teacher_id", "=", int(request.env.user.id))]
        if kw.get("date", False):
            domain += [
                ("create_date", ">=", kw["date"] + " 00:00:00"),
                ("create_date", "<=", kw["date"] + " 23:59:59"),
            ]
        if kw.get("name", False):
            domain += [("name", "ilike", kw["name"])]
        fetched_user_assignment = (
            request.env["xe.assignment"].sudo().search_read(domain, offset=offset, limit=limit)
        )
        if not fetched_user_assignment:
            return {"user_assignment_details": [], "fetch_assignment_details": True}

        students_list = []
        for assignment in fetched_user_assignment:
            attachments = (
                request.env["ir.attachment"]
                .sudo()
                .search_read(
                    [
                        ("res_id", "=", assignment["id"]),
                        ("res_model", "=", "xe.assignment"),
                    ],
                    ["id", "name", "mimetype"],
                )
            )
            for attachment in attachments:
                att_name = attachment.get("name", False) and attachment.get(
                    "name"
                ).split(".")
                if att_name:
                    attachment["file_extension"] = "." + att_name[-1]
                else:
                    attachment["file_extension"] = ""
            assignment["attachments"] = attachments

            students = (
                request.env["xe.student"]
                .sudo()
                .search_read(
                    [("id", "in", assignment["student_ids"])],
                    ["id", "name", "roll_number", "email"],
                )
            )
            students_list.append(
                {
                    "assignment_id": assignment["id"],
                    "assignment_name": assignment["name"],
                    "attendes": students,
                }
            )

        return {
            "user_assignment_details": fetched_user_assignment,
            "student_ids": students_list,
        }

    @http.route(
        "/v1/web/dataset/fetch/assignment/submission/details", type="json", auth="user"
    )
    def fetch_assignment_submission_details(self, assignment_submission_id):
        fetched_assignment_submission = (
            request.env["xe.assignment.submission"]
            .sudo()
            .search_read([("id", "=", int(assignment_submission_id))])
        )
        if not fetched_assignment_submission:
            return {
                "assignment_submission_details": [],
                "fetch_assignment_submission_details": True,
            }
        return {
            "assignment_submission_details": fetched_assignment_submission,
        }

    @http.route(
        "/v1/web/dataset/remove/student/assignment/allocation", type="json", auth="user"
    )
    def RemoveStuden_from_assignment(self, assignment_id, student_id):
        try:
            query = (
                "select * from student_assignment_rel where assignment_id=%s and student_id=%s"
                % (assignment_id, student_id)
            )
            request.env.cr.execute(query)
            studend_available = request.env.cr.dictfetchall()
            if studend_available:
                query1 = (
                    "delete from student_assignment_rel where assignment_id=%s and student_id=%s"
                    % (assignment_id, student_id)
                )
                request.env.cr.execute(query1)
                affected_rows = request.env.cr.rowcount
                if affected_rows:
                    return {"Success": "studen removed from respective assignment"}
            else:
                return {
                    "not_found": "studen not allocated / not found to respective assignment"
                }
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    # Assignment Bottons

    @http.route("/v1/web/dataset/cancel/assignment", type="json", auth="user")
    def cancel_assignment(self, assignment_id):
        try:
            fetched_assignment = (
                request.env["xe.assignment"].sudo().browse(int(assignment_id))
            )

            if not fetched_assignment:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment.sudo().state == "draft":
                fetched_assignment.sudo().cancel()
            else:
                return {
                    "status": "Assignment is not in draft status so it "
                    "can't be setted as cancel or it's already in cancel"
                }
            if fetched_assignment.sudo().state == "cancel":
                return {"status": "Assignment setted to Cancelled state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    # Assignment Submission Button

    @http.route(
        "/v1/web/dataset/submit/assignment/submission", type="json", auth="user"
    )
    def submit_assignment_submission(self, assignment_submission_id):
        try:
            fetched_assignment_submission = (
                request.env["xe.assignment.submission"]
                .sudo()
                .browse(int(assignment_submission_id))
            )
            if not fetched_assignment_submission:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment_submission.sudo().state in (
                "draft",
                "change_request",
            ):
                fetched_assignment_submission.sudo().submit()
            else:
                return {
                    "status": "Assignment Submission is not in Draft,Change-Request status so it "
                    "can't be setted as Submitted or it's already in Submitted"
                }
            if fetched_assignment_submission.sudo().state == "submitted":
                return {"status": "Assignment Submission setted to Submitted state"}
            if fetched_assignment_submission.sudo().state == "late_submit":
                return {
                    "status": "Assignment Submission submitted but its late "
                    "submitted so setted as Late Submitted"
                }
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/v1/web/dataset/cancel/assignment/submission", type="json", auth="user"
    )
    def cancel_assignment_submission(self, assignment_submission_id):
        try:
            fetched_assignment_submission = (
                request.env["xe.assignment.submission"]
                .sudo()
                .browse(int(assignment_submission_id))
            )
            if not fetched_assignment_submission:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment_submission.sudo().state == "draft":
                fetched_assignment_submission.sudo().cancel()
            else:
                return {
                    "status": "Assignment Submission is not in Draft status so it "
                    "can't be setted as Cancelled or it's already in Cancelled"
                }
            if fetched_assignment_submission.sudo().state == "cancel":
                return {"status": "Assignment Submission setted to Cancelled state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/v1/web/dataset/reset/draft/assignment/submission", type="json", auth="user"
    )
    def ResetDraftAssignmentSubmission(self, assignment_submission_id):
        try:
            fetched_assignment_submission = (
                request.env["xe.assignment.submission"]
                .sudo()
                .browse(int(assignment_submission_id))
            )
            if not fetched_assignment_submission:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment_submission.sudo().state == "cancel":
                fetched_assignment_submission.sudo().reset_to_draft()
            else:
                return {
                    "status": "Assignment Submission is not in Cancelled "
                    "status so it can't be setted as Draft or it's already in Draft"
                }
            if fetched_assignment_submission.sudo().state == "draft":
                return {"status": "Assignment Submission setted to Draft state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/v1/web/dataset/change/request/assignment/submission", type="json", auth="user"
    )
    def change_request_assignment_submission(self, assignment_submission_id):
        try:
            fetched_assignment_submission = (
                request.env["xe.assignment.submission"]
                .sudo()
                .browse(int(assignment_submission_id))
            )
            if not fetched_assignment_submission:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment_submission.sudo().state in (
                "draft",
                "submitted",
                "late_submit",
            ):
                fetched_assignment_submission.sudo().change_request()
            else:
                return {
                    "status": "Assignment Submission is not in Draft,Submitted,Late Submitted "
                    "status so it can't be setted as Change Request "
                    "or it's already in Change Request"
                }
            if fetched_assignment_submission.sudo().state == "change_request":
                return {
                    "status": "Assignment Submission setted to Change Request state"
                }
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/v1/web/dataset/accept/assignment/submission", type="json", auth="user"
    )
    def accept_assignment_submission(self, assignment_submission_id):
        try:
            fetched_assignment_submission = (
                request.env["xe.assignment.submission"]
                .sudo()
                .browse(int(assignment_submission_id))
            )
            if not fetched_assignment_submission:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment_submission.sudo().state in (
                "submitted",
                "late_submit",
            ):
                fetched_assignment_submission.sudo().accept()
            else:
                return {
                    "status": "Assignment Submission is not in Submitted,Late-Submit status "
                    "so it can't be setted as Accepted or it's already in Accepted"
                }
            if fetched_assignment_submission.sudo().state == "accepted":
                return {"status": "Assignment Submission setted to Accepted state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route("/v1/web/dataset/assignment/search_read", type="json", auth="user")
    def get_assignment_list(self, args):
        assignments_list = []
        assignments = request.env["xe.assignment"].search(args[0])
        for res in assignments:
            assignment = {}
            assignment.setdefault("id", [res.id, res.name])
            assignment.setdefault("name", res.name)
            assignment.setdefault("state", res.state)
            assignment.setdefault("course_id", [res.course_id.id, res.course_id.name])
            assignment.setdefault("term_id", [res.term_id.id, res.term_id.name])

            assignment.setdefault(
                "subject_id", [res.subject_id.id, res.subject_id.name]
            )
            assignment.setdefault(
                "assignment_type_id",
                [res.assignment_type_id.id, res.assignment_type_id.name],
            )
            assignment.setdefault(
                "faculty_id", [res.create_uid.id, res.create_uid.name]
            )
            assignment.setdefault("reviewer", False)
            assignment.setdefault("issued_date", res.issue_date)
            assignment.setdefault("marks", res.total_marks)
            assignment.setdefault("submission_date", res.submit_date)
            assignment.setdefault("description", res.description)

            student_ids = []
            assignment_sub_line = []

            [
                student_ids.append(
                    {"id": al.id, "roll_number": al.roll_number, "name": al.name}
                )
                for al in res.student_ids
            ]
            submission_ids = (
                request.env["xe.assignment.submission"]
                .sudo()
                .search([("assignment_id", "=", res.id)])
            )
            if submission_ids:
                [
                    assignment_sub_line.append(
                        {
                            "id": sl.id,
                            "student_id": [sl.student_id.id, sl.student_id.name],
                            "state": sl.state,
                            "submission_date": sl.submit_date,
                            "marks_on_submit": sl.marks_on_submit,
                        }
                    )
                    for sl in submission_ids
                ]

            assignment.setdefault("student_ids", student_ids)
            assignment.setdefault("assignment_sub_line", assignment_sub_line)

            assignments_list.append(assignment)

        return assignments_list

    @http.route("/v1/web/dataset/xe/assignment", type="json", auth="user")
    def get_assignment_by_id(self, assignment_id, fields):
        assignments = []
        assignment = request.env["xe.assignment"].search_read(
            [("id", "=", assignment_id)], fields
        )
        if assignment:
            attachments = request.env["ir.attachment"].search_read(
                [("res_id", "=", assignment_id), ("res_model", "=", "xe.assignment")],
                ["id", "name", "mimetype", "file_size"],
            )
            temp = assignment[0]
            temp["attachment_ids"] = attachments
            assignments = [temp]
        return assignments

    # Assignments APIs

    @http.route("/parent/student/assignments", type="json", auth="user")
    def get_parent_student_assignment(self, **kw):
        if not kw.get("partner_id", False):
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "partner_id Required",
                }
            }
        assignment_data = []
        student = (
            request.env["xe.student"]
            .sudo()
            .search([("partner_id", "=", int(kw["partner_id"]))], limit=1)
        )
        if student:
            assignments = self.get_assignmentlines(student)
            for rec in assignments:
                domain = [
                    ("id", "=", int(rec["assignment_id"])),
                    ("state", "in", ["assigned", "done"]),
                ]
                if kw.get("date", False):
                    domain += [
                        ("create_date", ">=", kw["date"] + " 00:00:00"),
                        ("create_date", "<=", kw["date"] + " 23:59:59"),
                    ]
                if kw.get("name", False):
                    domain += [("name", "ilike", kw["name"])]
                assignment = request.env["xe.assignment"].sudo().search_read(domain)
                attachments = (
                    request.env["ir.attachment"]
                    .sudo()
                    .search_read(
                        [
                            ("res_id", "=", int(rec["assignment_id"])),
                            ("res_model", "=", "xe.assignment"),
                        ],
                        ["id", "name", "mimetype"],
                    )
                )
                if assignment:
                    for attachment in attachments:
                        att_name = attachment.get("name", False) and attachment.get(
                            "name"
                        ).split(".")
                        if att_name:
                            attachment["file_extension"] = "." + att_name[-1]
                        else:
                            attachment["file_extension"] = ""
                    assignment[0]["attachments"] = attachments
                    assignment_data.append(assignment)
        if not assignment_data:
            return {"assignment_data": [], "fetch_assignment": True}
        return assignment_data

    def get_assignmentlines(self, student):
        query = (
            "select assignment_id from student_assignment_rel where student_id=%s"
            % (student.id)
        )
        request.cr.execute(query)
        assignment_ids = request.cr.dictfetchall()
        return assignment_ids

    @http.route("/assignment/searchby", type="json", auth="user")
    def get_assignment_searchby(self, **kw):
        domain = []
        if kw.get("date", False):
            domain += [
                ("create_date", ">=", kw["date"] + " 00:00:00"),
                ("create_date", "<=", kw["date"] + " 23:59:59"),
            ]
        if kw.get("name", False):
            domain += [("name", "ilike", kw["name"])]

        assignment = request.env["xe.assignment"].sudo().search_read(domain)
        if assignment:
            return assignment
        if not assignment:
            return [
                {
                    "message": "There are no assignment associated with the "
                    "search criteria entered."
                }
            ]

    @http.route(
        "/attachment/download/<int:attachment_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def download_attachment_assignment(self, attachment_id):
        """Check if this is a valid attachment id"""
        attachment = (
            request.env["ir.attachment"]
            .sudo()
            .search([("id", "=", int(attachment_id))])
        )

        if attachment:
            attachment = attachment[0]
        else:
            result_dict = {"Success": "Assignment Not Found!!!"}
            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
            return result

        if attachment["type"] == "url":
            if attachment["url"]:
                return redirect(attachment["url"])
            return request.not_found()
        if attachment["datas"]:
            data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment["name"], as_attachment=True)
        return request.not_found()

    @http.route(
        "/v1/web/dataset/create/assignment/submission", type="json", auth="user"
    )
    def create_assignment_submission(self, args):
        try:
            assignment_sub_ids = []
            for rec in args:
                missing_fields = [
                    key
                    for key in ["assignment_id", "marks_on_submit", "description"]
                    if key not in rec
                ]
                if missing_fields:
                    return {
                        "error": "Mendatory fields %s not Found"
                        % (",".join(missing_fields))
                    }
                if not missing_fields:
                    vals = {
                        "assignment_id": int(rec["assignment_id"]),
                        "marks_on_submit": float(rec["marks_on_submit"]),
                        "description": rec["description"],
                    }
                    if "student_id" in rec:
                        vals.update({"student_id": int(rec["student_id"])})
                    else:
                        student_id = (
                            request.env["xe.student"]
                            .search([("user_id", "=", request.env.user.id)])
                            .id
                        )
                        if student_id:
                            vals.update({"student_id": student_id})
                        else:
                            return {
                                "Failed": "Students not found related to current user."
                            }

                    assignment_sub_id = (
                        request.env["xe.assignment.submission"].sudo().create(vals)
                    )
                    if assignment_sub_id:
                        assignment_sub_ids.append(assignment_sub_id.id)
            return {
                "record_id": assignment_sub_ids,
                "Success": "Assignment Submission created successfully",
            }

        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route("/v1/web/dataset/fetch/assignment/class", type="json", auth="user")
    def fetch_assignment_class(self):
        user = self.get_user_type()
        assignment_classes = request.env["xe.course"].search_read(
            [("company_id", "=", user.get("company_id"))]
        )
        for ass_class in assignment_classes:
            del ass_class["head_teacher_signature"]
        return {"assignment_classes": assignment_classes}

    @http.route("/v1/web/dataset/fetch/classrooms/class/base", type="json", auth="user")
    def fetch_assignment_classroom_class_base(self, class_id):
        classrooms_ids = (
            request.env["xe.classroom"]
            .sudo()
            .search_read([("course_id", "=", int(class_id))])
        )
        return {"classroom_ids": classrooms_ids}

    @http.route("/v1/web/dataset/fetch/subject/class/base", type="json", auth="user")
    def fetch_assignment_subject(self, class_id):
        subject_ids = (
            request.env["xe.subject"]
            .sudo()
            .search_read([("course_ids", "in", [int(class_id)])])
        )
        return {"subject_ids": subject_ids}

    @http.route("/v1/web/dataset/fetch/assignment/type", type="json", auth="user")
    def fetch_assignment_type(self):
        user = self.get_user_type()
        assignment_types = request.env["xe.assignment.type"].search_read(
            [("company_id", "=", user.get("company_id"))]
        )
        return {"assignment_types": assignment_types}

    @http.route("/v1/web/dataset/fetch/students/class/base", type="json", auth="user")
    def fetch_assignment_student(self, **kw):
        if "class_id" not in kw:
            return {"In request Course/Class(class_id) is Required"}
        if "classroom_id" in kw:
            students = (
                request.env["xe.student"]
                .sudo()
                .search_read(
                    [
                        ("course_id", "=", kw["class_id"]),
                        ("classroom_id", "=", kw["classroom_id"]),
                    ]
                )
            )
        else:
            students = (
                request.env["xe.student"]
                .sudo()
                .search_read([("course_id", "=", kw["class_id"])])
            )
        return {"students_ids": students}

    @http.route("/v1/web/dataset/assign/assignment", type="json", auth="user")
    def assign_assignment(self, assignment_id):
        try:
            fetched_assignment = (
                request.env["xe.assignment"].sudo().browse(int(assignment_id))
            )
            if not fetched_assignment:
                return {
                    "note": "Assignment Not found!!",
                    "fetched_assignment_details": [],
                }
            if not fetched_assignment.student_ids:
                return {"status": "Please Allocate Students to assignment"}
            if fetched_assignment.sudo().state == "draft":
                fetched_assignment.sudo().assign()
            else:
                return {
                    "status": "Assignment is not in draft status so it can't be setted as "
                    "Assign or it's already in assign"
                }
            if fetched_assignment.sudo().state == "assigned":
                return {"status": "Assignment setted to assigned state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route("/v1/web/dataset/done/assignment", type="json", auth="user")
    def done_assignment(self, assignment_id):
        try:
            fetched_assignment = (
                request.env["xe.assignment"].sudo().browse(int(assignment_id))
            )
            if not fetched_assignment:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment.sudo().state == "assigned":
                fetched_assignment.sudo().assignment_as_done()
            else:
                return {
                    "status": "Assignment is not in assigned status so it can't be "
                    "setted as Done or it's already in Done"
                }
            if fetched_assignment.sudo().state == "done":
                return {"status": "Assignment setted to Done state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/v1/web/dataset/create/assignment/<string:name>/<int:assignment_type_id>/<int:class_id>/<string:classroom_id>/<int:subject_id>/<int:total_marks>/<string:submit_date>/<string:student_ids>/<string:description>",
        csrf=False,
        auth="user",
    )
    def create_new_assignment(
        self,
        name,
        assignment_type_id,
        class_id,
        classroom_id,
        subject_id,
        total_marks,
        submit_date,
        student_ids,
        description,
    ):
        try:
            classroom_id = classroom_id.replace("[", "").replace("]", "")
            list_of_student = []
            if student_ids and len(student_ids) > 2:
                for i in student_ids.replace("[", "").replace("]", "").split(","):
                    list_of_student.append(int(i))
            vals = {
                "name": name,
                "assignment_type_id": int(assignment_type_id),
                "course_id": int(class_id),
                "subject_id": int(subject_id),
                "submit_date": submit_date,
                "total_marks": float(total_marks),
                "description": description,
                "classroom_id": classroom_id and int(classroom_id) or False,
                "student_ids": [(6, 0, list_of_student)] if list_of_student else False,
            }
            assignment_id = request.env["xe.assignment"].sudo().create(vals)
            attachments = []
            if assignment_id:
                for key, val in http.request.httprequest.files.items():
                    ir_attachment = request.env["ir.attachment"]
                    attachment = ir_attachment.sudo().create(
                        {
                            "name": val.filename,
                            "datas": base64.b64encode(val.read()),
                            "res_model": assignment_id._name,
                            "res_id": assignment_id.id,
                        }
                    )
                    attachments.append(attachment)

            result_dict = {
                "record_id": assignment_id.id,
                "attachments": [attachment.id for attachment in attachments],
                "Success": "Assignment created successfully",
            }
            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }
            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/dataset/upload/attachment/create/submission/<int:assignment_id>/<int:student_id>/<int:marks>/<string:description>",
        csrf=False,
        auth="user",
    )
    def create_assignment_submission(
        self, file, assignment_id, student_id, marks, description
    ):
        try:
            vals = {
                "assignment_id": int(assignment_id),
                "student_id": int(student_id),
                "marks_on_submit": float(marks),
                "description": description,
            }

            assignment_sub_id = (
                request.env["xe.assignment.submission"].sudo().create(vals)
            )
            if assignment_sub_id:
                for key, val in http.request.httprequest.files.items():
                    ir_attachment = request.env["ir.attachment"]
                    attachment = ir_attachment.sudo().create(
                        {
                            "name": val.filename,
                            "datas": base64.b64encode(val.read()),
                            "res_model": assignment_sub_id._name,
                            "res_id": assignment_sub_id.id,
                        }
                    )

            result_dict = {
                "assignment_submission_id": assignment_sub_id.id,
                "Success": "Assignment Submission created successfully",
            }
            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }
            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )

        return result

    @http.route("/v1/web/dataset/reset/draft/assignment", type="json", auth="user")
    def reset_to_draft_assignment(self, assignment_id):
        try:
            fetched_assignment = (
                request.env["xe.assignment"].sudo().browse(int(assignment_id))
            )

            if not fetched_assignment:
                return {
                    "fetched_assignment_details": [],
                }
            if fetched_assignment.sudo().state == "assigned":
                fetched_assignment.sudo().reset_to_draft()
            else:
                return {
                    "status": "Assignment is not in Cancel status so it can't be setted as "
                    "Draft or it's already in Draft"
                }
            if fetched_assignment.sudo().state == "draft":
                return {"status": "Assignment setted to Draft state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/web/fetch/assignment/based/assignment/submission/details",
        type="json",
        auth="user",
    )
    def fetch_base_assignment_submission_details(self, assignment_id):
        fetched_assignment_submission = (
            request.env["xe.assignment.submission"]
            .sudo()
            .search_read([("assignment_id", "=", int(assignment_id))])
        )
        if not fetched_assignment_submission:
            return {"assignment_submissions": [], "fetch_submission_details": True}
        return {"assignment_submissions": fetched_assignment_submission}

    @http.route("/assignment/edit", csrf=False, auth="user")
    def assignment_edit_new(self):
        pdfhttpheaders = [
            ("Content-Type", "application/json"),
        ]

        values = {}
        list_of_student = []
        for key, val in http.request.httprequest.form.items():
            if key == "student_ids":
                if val:
                    for i in val.replace("[", "").replace("]", "").split(","):
                        list_of_student.append(int(i))
                continue
            if val.isdigit():
                values[key] = int(val)
                continue
            values[key] = val

        assignment_id = request.env["xe.assignment"].search(
            [("id", "=", values.get("id"))], limit=1
        )
        if not assignment_id:
            result = request.make_response(
                json.dumps({"message": "Assignment not found."}), headers=pdfhttpheaders
            )
            return result
        if assignment_id.state != "draft":
            result = request.make_response(
                json.dumps({"message": "Assignment not in draft state."}),
                headers=pdfhttpheaders,
            )
            return result

        try:
            assignment = assignment_id.write(values)
            if list_of_student:
                for student in list_of_student:
                    assignment_id.student_ids = [(4, student)]
            for key, val in http.request.httprequest.files.items():
                ir_attachment = request.env["ir.attachment"]
                attachment = ir_attachment.sudo().create(
                    {
                        "name": val.filename,
                        "datas": base64.b64encode(val.read()),
                        "res_model": assignment_id._name,
                        "res_id": assignment_id.id,
                    }
                )
            result = request.make_response(
                json.dumps({"message": "Assignment update successfully."}),
                headers=pdfhttpheaders,
            )
            return result
        except Exception as e:
            result = request.make_response(
                json.dumps({"message": str(e)}), headers=pdfhttpheaders
            )
            return result

    @http.route(
        "/parent/student/submission/details",
        type="json",
        auth="user",
    )
    def get_parent_student_submission_details(self, **kw):
        assignment_submission = (
            request.env["xe.assignment.submission"]
            .sudo()
            .search_read(
                [
                    ("student_id", "=", kw.get("student_id")),
                    ("assignment_id", "=", kw.get("assignment_id")),
                ],
                [
                    "name",
                    "student_id",
                    "assignment_id",
                    "marks_on_submit",
                    "description",
                    "state",
                ],
            )
        )

        if assignment_submission:
            for submission in assignment_submission:
                attachments = (
                    request.env["ir.attachment"]
                    .sudo()
                    .search_read(
                        [
                            ("res_id", "=", submission.get("id")),
                            ("res_model", "=", "xe.assignment.submission"),
                        ],
                        ["id", "name", "mimetype"],
                    )
                )
                for attachment in attachments:
                    att_name = attachment.get("name", False) and attachment.get(
                        "name"
                    ).split(".")
                    if att_name:
                        attachment["file_extension"] = "." + att_name[-1]
                    else:
                        attachment["file_extension"] = ""
                submission["attachments"] = attachments

        if not assignment_submission:
            return {"assignment_submissions": []}
        return {"assignment_submissions": assignment_submission}

    @http.route(
        "/assignment/submission/edit",
        csrf=False,
        auth="user",
    )
    def assignment_submission_edit(self):
        pdfhttpheaders = [
            ("Content-Type", "application/json"),
        ]
        values = {}
        for key, val in http.request.httprequest.form.items():
            if val.isdigit():
                values[key] = int(val)
                continue
            values[key] = val

        assignment_sub_id = (
            request.env["xe.assignment.submission"]
            .sudo()
            .search([("id", "=", values.get("id"))], limit=1)
        )

        if not assignment_sub_id:
            result = request.make_response(
                json.dumps({"message": "Assignment submission not found."}),
                headers=pdfhttpheaders,
            )
            return result

        try:
            if assignment_sub_id:
                for key, val in http.request.httprequest.files.items():
                    ir_attachment = request.env["ir.attachment"]
                    attachment = ir_attachment.sudo().create(
                        {
                            "name": val.filename,
                            "datas": base64.b64encode(val.read()),
                            "res_model": assignment_sub_id._name,
                            "res_id": assignment_sub_id.id,
                        }
                    )
            result_dict = {
                "assignment_submission_id": assignment_sub_id.id,
                "message": "Assignment submission update successfully",
            }
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }
        result = request.make_response(json.dumps(result_dict), headers=pdfhttpheaders)
        return result
