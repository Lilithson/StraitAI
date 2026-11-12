from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

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


class StudentManagementViewTests(TestCase):
    def setUp(self):
        self.program = Program.objects.create(code="CSE", name="Computer Science")
        self.department_head = User.objects.create_superuser(username="head", password="StrongPassword123")
        self.client.force_login(self.department_head)

    def test_department_head_can_create_a_student_account_and_profile(self):
        response = self.client.post(
            reverse("accounts:student-add"),
            {
                "username": "student1",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "student_number": "20260002",
                "program": self.program.pk,
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            },
        )

        self.assertRedirects(response, reverse("accounts:students"))
        self.assertTrue(StudentProfile.objects.filter(student_number="20260002").exists())
        user = User.objects.get(username="student1")
        self.assertTrue(user.groups.filter(name="Student").exists())


class StudentPortalTests(TestCase):
    def setUp(self):
        program = Program.objects.create(code="CSE", name="Computer Science")
        course = Course.objects.create(
            program=program, code="CSE201", title="Data Structures", credit_hours=3
        )
        term = AcademicTerm.objects.create(year=2026, season=AcademicTerm.Season.FALL)
        offering = CourseOffering.objects.create(course=course, term=term, section="1")
        self.student_user = User.objects.create_user(username="student", password="StrongPassword123")
        self.student = StudentProfile.objects.create(
            user=self.student_user, program=program, student_number="20260010"
        )
        Enrollment.objects.create(student=self.student, offering=offering)

    def test_student_portal_shows_only_the_signed_in_students_workspace(self):
        self.client.force_login(self.student_user)

        response = self.client.get(reverse("accounts:student-portal"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My learning")
        self.assertContains(response, "CSE201")
        self.assertContains(response, "20260010")

    def test_student_login_redirects_to_their_portal(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "student", "password": "StrongPassword123"},
        )

        self.assertRedirects(response, reverse("accounts:student-portal"))
