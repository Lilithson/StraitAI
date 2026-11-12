from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Enrollment, StudentProfile
from accounts.roles import (
    DEFAULT_ROLE_NAMES,
    ROLE_DEPARTMENT_HEAD,
    ROLE_INSTRUCTOR,
    can_manage_offering,
)
from academics.models import AcademicTerm, Course, CourseOffering, Program


class EnrollmentTests(TestCase):
    def setUp(self):
        self.program = Program.objects.create(code="CSE", name="Computer Science")
        self.course = Course.objects.create(
            program=self.program, code="CSE311", title="Software Engineering", credit_hours=3
        )
        self.term = AcademicTerm.objects.create(year=2026, season=AcademicTerm.Season.FALL)
        self.offering = CourseOffering.objects.create(course=self.course, term=self.term, section="1")
        self.student_user = User.objects.create_user(username="student")
        self.student = StudentProfile.objects.create(
            user=self.student_user, program=self.program, student_number="20260001"
        )

    def test_each_default_role_group_exists(self):
        self.assertEqual(
            set(Group.objects.filter(name__in=DEFAULT_ROLE_NAMES).values_list("name", flat=True)),
            set(DEFAULT_ROLE_NAMES),
        )

    def test_student_can_only_be_enrolled_once_per_offering(self):
        Enrollment.objects.create(student=self.student, offering=self.offering)

        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=self.student, offering=self.offering)

    def test_only_an_assigned_instructor_or_department_head_can_manage_an_offering(self):
        instructor = User.objects.create_user(username="instructor")
        instructor.groups.add(Group.objects.get(name=ROLE_INSTRUCTOR))
        self.offering.instructors.add(instructor)
        department_head = User.objects.create_user(username="head")
        department_head.groups.add(Group.objects.get(name=ROLE_DEPARTMENT_HEAD))

        self.assertTrue(can_manage_offering(instructor, self.offering))
        self.assertTrue(can_manage_offering(department_head, self.offering))
        self.assertFalse(can_manage_offering(self.student_user, self.offering))
