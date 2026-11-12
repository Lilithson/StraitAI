"""Create a small, repeatable StraitAI demonstration dataset."""

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Enrollment, StudentProfile
from accounts.roles import ROLE_DEPARTMENT_HEAD, ROLE_INSTRUCTOR, ROLE_STUDENT
from academics.models import (
    AcademicTerm,
    Course,
    CourseOffering,
    CourseProgramOutcomeMapping,
    LearningOutcome,
    LearningOutcomeProgramOutcomeMapping,
    Program,
    ProgramOutcome,
)
from assessments.models import Assessment, AssessmentLearningOutcomeMapping, Grade


DEMO_PASSWORD = "DemoPass123!"
STUDENTS = (
    ("demo.ada", "Ada", "Yilmaz", "D2026001"),
    ("demo.beren", "Beren", "Kaya", "D2026002"),
    ("demo.cem", "Cem", "Arslan", "D2026003"),
    ("demo.deniz", "Deniz", "Demir", "D2026004"),
    ("demo.elif", "Elif", "Aydin", "D2026005"),
    ("demo.furkan", "Furkan", "Sahin", "D2026006"),
)


class Command(BaseCommand):
    help = "Create idempotent demo users, academic data, assessments, mappings, and grades."

    @transaction.atomic
    def handle(self, *args, **options):
        groups = {
            name: Group.objects.get_or_create(name=name)[0]
            for name in (ROLE_STUDENT, ROLE_INSTRUCTOR, ROLE_DEPARTMENT_HEAD)
        }

        department_head = self._get_user(
            username="demo.head",
            first_name="Demir",
            last_name="Koc",
            is_staff=True,
        )
        department_head.groups.add(groups[ROLE_DEPARTMENT_HEAD])

        instructor = self._get_user(
            username="demo.instructor",
            first_name="Ipek",
            last_name="Aslan",
        )
        instructor.groups.add(groups[ROLE_INSTRUCTOR])

        program, _ = Program.objects.get_or_create(
            code="DEMO-CSE", defaults={"name": "Demo Computer Science"}
        )
        term, _ = AcademicTerm.objects.get_or_create(
            year=2026, season=AcademicTerm.Season.FALL
        )

        po1, _ = ProgramOutcome.objects.get_or_create(
            program=program,
            code="PO1",
            defaults={"description": "Apply computing and problem-solving knowledge."},
        )
        po2, _ = ProgramOutcome.objects.get_or_create(
            program=program,
            code="PO2",
            defaults={"description": "Design and evaluate software-based solutions."},
        )

        foundations, _ = Course.objects.get_or_create(
            program=program,
            code="DCS210",
            defaults={"title": "Data Foundations", "credit_hours": 3},
        )
        analytics, _ = Course.objects.get_or_create(
            program=program,
            code="DCS315",
            defaults={"title": "Learning Analytics", "credit_hours": 3},
        )
        foundations_offering, _ = CourseOffering.objects.get_or_create(
            course=foundations, term=term, section="1"
        )
        analytics_offering, _ = CourseOffering.objects.get_or_create(
            course=analytics, term=term, section="1"
        )
        foundations_offering.instructors.add(instructor)
        analytics_offering.instructors.add(instructor)

        foundation_lo1 = self._get_learning_outcome(
            foundations, "LO1", "Model structured data for an application."
        )
        foundation_lo2 = self._get_learning_outcome(
            foundations, "LO2", "Write and explain database queries."
        )
        analytics_lo1 = self._get_learning_outcome(
            analytics, "LO1", "Interpret student performance data."
        )
        analytics_lo2 = self._get_learning_outcome(
            analytics, "LO2", "Communicate outcome-based findings."
        )

        self._map_learning_outcome(foundation_lo1, po1, "2.000")
        self._map_learning_outcome(foundation_lo2, po1, "1.000")
        self._map_learning_outcome(foundation_lo2, po2, "2.000")
        self._map_learning_outcome(analytics_lo1, po1, "1.000")
        self._map_learning_outcome(analytics_lo1, po2, "2.000")
        self._map_learning_outcome(analytics_lo2, po2, "2.000")
        self._map_course(foundations, po1, "4.0")
        self._map_course(foundations, po2, "3.0")
        self._map_course(analytics, po1, "3.0")
        self._map_course(analytics, po2, "4.0")

        students = []
        for username, first_name, last_name, student_number in STUDENTS:
            user = self._get_user(username, first_name, last_name)
            user.groups.add(groups[ROLE_STUDENT])
            student, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={"program": program, "student_number": student_number},
            )
            students.append(student)

        foundation_enrollments = self._enroll_students(students, foundations_offering)
        analytics_enrollments = self._enroll_students(students, analytics_offering)

        foundation_assessments = self._create_foundations_assessments(
            foundations_offering, foundation_lo1, foundation_lo2
        )
        analytics_assessments = self._create_analytics_assessments(
            analytics_offering, analytics_lo1, analytics_lo2
        )
        self._create_grades(
            foundation_assessments,
            foundation_enrollments,
            ((17, 78, 42), (15, 68, 36), (19, 91, 46), (14, 63, 32), (18, 84, 40), (16, 74, 38)),
        )
        self._create_grades(
            analytics_assessments,
            analytics_enrollments,
            ((18, 82, 43), (14, 71, 35), (19, 94, 47), (15, 66, 34), (17, 86, 41), (16, 77, 39)),
        )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Department Head: demo.head / DemoPass123!")
        self.stdout.write("Instructor: demo.instructor / DemoPass123!")
        self.stdout.write("Students: demo.ada through demo.furkan / DemoPass123!")
        self.stdout.write("Use /assessments/ to demonstrate grades, LO scores, and PO scores.")

    @staticmethod
    def _get_user(username, first_name, last_name, is_staff=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": is_staff,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password"])
        return user

    @staticmethod
    def _get_learning_outcome(course, code, description):
        learning_outcome, _ = LearningOutcome.objects.get_or_create(
            course=course, code=code, defaults={"description": description}
        )
        return learning_outcome

    @staticmethod
    def _map_learning_outcome(learning_outcome, program_outcome, weight):
        LearningOutcomeProgramOutcomeMapping.objects.get_or_create(
            learning_outcome=learning_outcome,
            program_outcome=program_outcome,
            defaults={"weight": Decimal(weight)},
        )

    @staticmethod
    def _map_course(course, program_outcome, weight):
        CourseProgramOutcomeMapping.objects.get_or_create(
            course=course,
            program_outcome=program_outcome,
            defaults={"weight": Decimal(weight)},
        )

    @staticmethod
    def _enroll_students(students, offering):
        enrollments = []
        for student in students:
            enrollment, _ = Enrollment.objects.get_or_create(
                student=student,
                offering=offering,
                defaults={"status": Enrollment.Status.ENROLLED},
            )
            enrollments.append(enrollment)
        return enrollments

    def _create_foundations_assessments(self, offering, lo1, lo2):
        quiz = self._get_assessment(offering, "Quiz 1", Assessment.Kind.QUIZ, "20.00", date(2026, 9, 20))
        midterm = self._get_assessment(
            offering, "Midterm", Assessment.Kind.EXAM, "100.00", date(2026, 10, 25)
        )
        project = self._get_assessment(
            offering, "Database project", Assessment.Kind.PROJECT, "50.00", date(2026, 12, 1)
        )
        self._map_assessment(quiz, lo1, "1.000")
        self._map_assessment(midterm, lo1, "2.000")
        self._map_assessment(midterm, lo2, "1.000")
        self._map_assessment(project, lo2, "2.000")
        return (quiz, midterm, project)

    def _create_analytics_assessments(self, offering, lo1, lo2):
        quiz = self._get_assessment(offering, "Quiz 1", Assessment.Kind.QUIZ, "20.00", date(2026, 9, 22))
        midterm = self._get_assessment(
            offering, "Midterm", Assessment.Kind.EXAM, "100.00", date(2026, 10, 28)
        )
        project = self._get_assessment(
            offering, "Analytics report", Assessment.Kind.PROJECT, "50.00", date(2026, 12, 5)
        )
        self._map_assessment(quiz, lo1, "1.000")
        self._map_assessment(midterm, lo1, "2.000")
        self._map_assessment(midterm, lo2, "1.000")
        self._map_assessment(project, lo2, "2.000")
        return (quiz, midterm, project)

    @staticmethod
    def _get_assessment(offering, title, kind, max_score, due_date):
        assessment, _ = Assessment.objects.get_or_create(
            offering=offering,
            title=title,
            defaults={"kind": kind, "max_score": Decimal(max_score), "due_date": due_date},
        )
        return assessment

    @staticmethod
    def _map_assessment(assessment, learning_outcome, weight):
        AssessmentLearningOutcomeMapping.objects.get_or_create(
            assessment=assessment,
            learning_outcome=learning_outcome,
            defaults={"weight": Decimal(weight)},
        )

    @staticmethod
    def _create_grades(assessments, enrollments, rows):
        for enrollment, scores in zip(enrollments, rows, strict=True):
            for assessment, score in zip(assessments, scores, strict=True):
                Grade.objects.get_or_create(
                    assessment=assessment,
                    enrollment=enrollment,
                    defaults={"score": Decimal(str(score))},
                )
