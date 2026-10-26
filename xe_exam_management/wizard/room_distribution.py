# -*- coding: utf-8 -*-

from odoo import models, api, fields, exceptions, _


class XeRoomDistribution(models.TransientModel):
    _name = "xe.room.distribution"
    _description = " Exam Room Distribution "

    @api.depends("student_ids")
    def _compute_get_total_student(self):
        for record in self:
            total_student = 0
            if record.student_ids:
                total_student = len(record.student_ids)
            record.total_student = total_student

    @api.depends("room_ids", "room_ids.capacity")
    def _compute_get_room_capacity(self):
        for record in self:
            room_capacity = 0
            if record.room_ids:
                for room in record.room_ids:
                    room_capacity += room.capacity or 0
            record.room_capacity = room_capacity

    exam_id = fields.Many2one("xe.exam", "Exam")
    subject_id = fields.Many2one("xe.subject", "Subject")
    name = fields.Char("Exam")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    exam_session_id = fields.Many2one("xe.exam.session")
    course_id = fields.Many2one("xe.course", "Class")
    term_id = fields.Many2one("xe.term", "Term")
    academic_term_id = fields.Many2one("xe.academic.terms")
    total_student = fields.Integer(compute="_compute_get_total_student")
    room_capacity = fields.Integer(compute="_compute_get_room_capacity")
    room_ids = fields.Many2many("xe.exam.room", string="Exam Rooms")
    student_ids = fields.Many2many("xe.student", string="Student")

    @api.model
    def default_get(self, fields):
        res = super(XeRoomDistribution, self).default_get(fields)
        active_id = self.env.context.get("active_id", False)
        exam = self.env["xe.exam"].browse(active_id)
        session = exam.session_id
        domain = []
        if exam.session_id.course_id:
            domain.append(("course_id", "=", exam.session_id.course_id.id))
        if exam.session_id.classroom_ids:
            domain.append(("classroom_id", "in", exam.classroom_ids.ids))
        students = self.env["xe.student"].search(domain)
        student_ids = students.ids
        total_student = len(student_ids)
        res.update(
            {
                "exam_id": active_id,
                "name": exam.name,
                "start_time": exam.start_time,
                "end_time": exam.end_time,
                "exam_session_id": session.id,
                "course_id": session.course_id.id,
                "academic_term_id": session.academic_term_id.id,
                "total_student": total_student,
                "student_ids": [(6, 0, student_ids)],
            }
        )
        return res

    def schedule_exam(self):
        for exam in self:
            if exam.total_student > exam.room_capacity:
                raise exceptions.AccessError(
                    _("Room capacity must be greater than total number of student")
                )
            student_ids = []
            for student in exam.student_ids:
                student_ids.append(student.id)
            for room in exam.room_ids:
                for i in range(room.capacity):
                    if not student_ids:
                        continue
                    self.env["xe.exam.attendees"].create(
                        {
                            "exam_id": exam.exam_id.id,
                            "student_id": student_ids[0],
                            "status": "present",
                            "course_id": exam.course_id.id,
                            "term_id": exam.term_id.id,
                            "room_id": room.id,
                        }
                    )
                    student_ids.remove(student_ids[0])
            exam.exam_id.state = "schedule"
            return True
