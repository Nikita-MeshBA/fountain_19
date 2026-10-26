# pylint: disable=E0401,C0114,C0115,C0116
import base64
import json

from odoo.http import request

from odoo import http


class EnquiryRegistration(http.Controller):

    @http.route('/get/courses', type='json', auth='public',methods=['POST'])
    def handle_password_request(self, **post):
        school_id = post.get('school')
        if school_id:
            course_ids =request.env["xe.course"].sudo().search([('company_id','=',int(school_id))]),
        course_ids_list = []
        course_ids_list.append({
            'name': '',
            'id': '',
        })
        if course_ids:
            for line in course_ids[0]:
                course_ids_list.append({
                    'name': line.name,
                    'id': line.id,
                })
        return course_ids_list

    @http.route(["/enquiry/form"], type="http", auth="public", website=True)
    def enquiry_form(self):
        render_values = {
            "countries": request.env["res.country"].sudo().search([]),
            "course_ids": request.env["xe.course"].sudo().search([('company_id','=',request.env.company.id)]),
            "states": request.env["res.country.state"].sudo().search([]),
            "school_ids": request.env["res.company"].sudo().search([]),
            "default_school": request.env.company
        }
        return request.render(
            "xe_online_admission_management.tmp_enquiry_form", render_values
        )

    @http.route(["/enquiry/form/submit"], type="http", auth="public", website=True)
    def enquiry_form_submit(self, **post):
        p1_name = post.get("p1_name")
        p1_email = post.get("p1_email")
        p1_birth_date = post.get("p1_birth_date")
        p1_phone = post.get("p1_phone")
        p2_name = post.get("p2_name")
        p2_email = post.get("p2_email")
        p2_birth_date = post.get("p2_birth_date")
        p2_phone = post.get("p2_phone")
        p1_relation = post.get("p1_relation")
        p2_relation = post.get("p2_relation")
        school_id = post.get("school_id")

        gender_map = {"m": "male", "f": "female"}

        p1_gender = gender_map.get(post.get("p1_gender", "").lower(), "")
        p2_gender = gender_map.get(post.get("p2_gender", "").lower(), "")

        vals = {
            "name": post.get("name"),
            "nationality_id": post.get("nationality_id"),
            "country_id": post.get("country_id"),
            "gender": gender_map.get(post.get("gender", "").lower(), ""),
            "email": post.get("email"),
            "dob": post.get("birth_date"),
            "course_id": post.get("course_id"),
            "previous_school_attended": post.get("previous_school"),
            "previous_school_mark": post.get("previous_school_marks"),
            "street": post.get("street"),
            "city": post.get("city"),
            "zip": post.get("zip"),
            "state_id": post.get("state_id"),
            "county": post.get("county"),
            "doc_type": "online",
            "company_id":int(school_id)
        }
        if post.get("sibling_admission"):
            sibling_id = (
                request.env["xe.student"]
                .sudo()
                .search([("roll_number", "=", post.get("sibling_admission"))])
            )
            if sibling_id:
                vals["is_sibling"] = True
                vals["student_ids"] = [(6, 0, sibling_id.ids)]
                student_parent_recs = (
                    request.env["xe.student.parent"]
                    .sudo()
                    .search([("student_id", "=", sibling_id.id)])
                )
                if student_parent_recs:
                    parent_ids = student_parent_recs.mapped("parent_id").ids
                    vals["parent_ids"] = [(6, 0, parent_ids)]
        else:
            parent_lines = []
            parent1_vals = {}
            parent2_vals = {}
            if p1_name:
                parent1_vals["name"] = p1_name
                if p1_email:
                    parent1_vals["email"] = p1_email
                if p1_gender:
                    parent1_vals["gender"] = p1_gender
                if p1_phone:
                    parent1_vals["phone"] = p1_phone
                if p1_relation:
                    parent1_vals["relation"] = p1_relation
                if p1_birth_date:
                    parent1_vals["dob"] = p1_birth_date
                parent1_vals["company_id"] = int(school_id)
                if parent1_vals:
                    parent_lines.append((0, 0, parent1_vals))
            if p2_name:
                parent2_vals["name"] = p2_name
                if p2_email:
                    parent2_vals["email"] = p2_email
                if p2_gender:
                    parent2_vals["gender"] = p2_gender
                if p2_birth_date:
                    parent2_vals["dob"] = p2_birth_date
                if p2_phone:
                    parent2_vals["phone"] = p2_phone
                if p2_relation:
                    parent2_vals["relation"] = p2_relation
                parent2_vals["company_id"] = int(school_id)
                if parent2_vals:
                    parent_lines.append((0, 0, parent2_vals))
            if parent_lines:
                vals["parent_ids"] = parent_lines
        if post.get("birth_certificate_new"):
            vals["student_birthcert"] = base64.b64encode(
                post.get("birth_certificate_new").read()
            )
            vals["store_fname1"] = post.get("birth_certificate_new").filename
        if post.get("report_card_copy"):
            vals["previous_term_report"] = base64.b64encode(
                post.get("report_card_copy").read()
            )
            vals["store_fname9"] = post.get("report_card_copy").filename
        if post.get("leaving_certificate"):
            vals["leaving_certificate"] = base64.b64encode(
                post.get("leaving_certificate").read()
            )
            vals["store_fname11"] = post.get("leaving_certificate").filename
        if post.get("national_parent1"):
            vals["father_passport"] = base64.b64encode(
                post.get("national_parent1").read()
            )
            vals["store_fname3"] = post.get("national_parent1").filename
        if post.get("national_parent2"):
            vals["mother_passport"] = base64.b64encode(
                post.get("national_parent2").read()
            )
            vals["store_fname4"] = post.get("national_parent2").filename
        if post.get("passportcopy_parent1"):
            vals["passportcopy_father"] = base64.b64encode(
                post.get("passportcopy_parent1").read()
            )
            vals["store_fname5"] = post.get("passportcopy_parent1").filename
        if post.get("passportcopy_parent2"):
            vals["passportcopy_mother"] = base64.b64encode(
                post.get("passportcopy_parent2").read()
            )
            vals["store_fname6"] = post.get("passportcopy_parent2").filename
        enquiry = request.env["xe.admission.enquiry"].sudo().create(vals)
        vals = {
            "enquiry": enquiry,
        }
        return request.render(
            "xe_online_admission_management.tmp_enquiry_form_success", vals
        )
