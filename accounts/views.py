from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from accounts.forms import EnrollmentForm, StudentCreationForm
from accounts.mixins import DepartmentHeadRequiredMixin
from accounts.models import Enrollment, StudentProfile
from accounts.roles import ROLE_DEPARTMENT_HEAD, ROLE_INSTRUCTOR, has_role
from assessments.models import Grade
from assessments.program_outcome_scoring import calculate_program_outcome_scores
from assessments.scoring import calculate_learning_outcome_scores


class RoleBasedLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"

    def get_default_redirect_url(self):
        user = self.request.user
        if StudentProfile.objects.filter(user=user).exists():
            return reverse("accounts:student-portal")
        if has_role(user, ROLE_DEPARTMENT_HEAD):
            return reverse("academics:setup")
        if has_role(user, ROLE_INSTRUCTOR):
            return reverse("assessments:list")
        return reverse("core:home")


class StudentManagementView(DepartmentHeadRequiredMixin, TemplateView):
    template_name = "accounts/student_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "students": StudentProfile.objects.select_related("user", "program"),
                "enrollments": Enrollment.objects.select_related(
                    "student__user", "offering__course", "offering__term"
                ),
            }
        )
        return context


class StudentCreateView(DepartmentHeadRequiredMixin, FormView):
    template_name = "accounts/student_form.html"
    form_class = StudentCreationForm
    success_url = reverse_lazy("accounts:students")

    def form_valid(self, form):
        profile = form.save()
        messages.success(self.request, f"Created student {profile.student_number}.")
        return super().form_valid(form)


class EnrollmentCreateView(DepartmentHeadRequiredMixin, CreateView):
    template_name = "accounts/enrollment_form.html"
    form_class = EnrollmentForm
    success_url = reverse_lazy("accounts:students")

    def form_valid(self, form):
        messages.success(self.request, "Created enrollment.")
        return super().form_valid(form)


class StudentPortalView(LoginRequiredMixin, TemplateView):
    """Read-only course and outcome evidence for the signed-in student."""

    template_name = "accounts/student_portal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = self.request.user.student_profile
        except StudentProfile.DoesNotExist as error:
            raise PermissionDenied("Only student accounts can open the student portal.") from error

        enrollments = list(
            Enrollment.objects.filter(student=student)
            .select_related("offering__course__program", "offering__term")
            .order_by("-offering__term__year", "offering__course__code")
        )
        course_cards = []
        recorded_grade_count = 0
        for enrollment in enrollments:
            grades = list(
                Grade.objects.filter(enrollment=enrollment)
                .select_related("assessment")
                .order_by("assessment__due_date", "assessment__title")
            )
            grade_rows = []
            for grade in grades:
                percentage = (grade.score / grade.assessment.max_score * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                grade_rows.append(
                    {
                        "assessment": grade.assessment,
                        "score": grade.score,
                        "maximum_score": grade.assessment.max_score,
                        "percentage": f"{percentage:.2f}%",
                    }
                )
            recorded_grade_count += len(grade_rows)

            _, learning_score_sets = calculate_learning_outcome_scores(enrollment.offering)
            learning_scores = next(
                (
                    score_set.scores
                    for score_set in learning_score_sets
                    if score_set.enrollment.pk == enrollment.pk
                ),
                (),
            )
            _, program_score_sets = calculate_program_outcome_scores(enrollment.offering)
            program_scores = next(
                (
                    score_set.scores
                    for score_set in program_score_sets
                    if score_set.enrollment.pk == enrollment.pk
                ),
                (),
            )
            course_cards.append(
                {
                    "enrollment": enrollment,
                    "grades": grade_rows,
                    "learning_scores": learning_scores,
                    "program_scores": program_scores,
                }
            )

        context.update(
            {
                "student": student,
                "course_cards": course_cards,
                "recorded_grade_count": recorded_grade_count,
                "active_course_count": sum(
                    enrollment.status == Enrollment.Status.ENROLLED for enrollment in enrollments
                ),
            }
        )
        return context
