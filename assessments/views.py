from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from accounts.mixins import DepartmentHeadRequiredMixin
from accounts.roles import ROLE_DEPARTMENT_HEAD, ROLE_INSTRUCTOR, can_manage_offering, has_role
from academics.models import CourseOffering
from assessments.access import can_manage_assessment, manageable_offerings
from assessments.forms import (
    AssessmentForm,
    AssessmentLearningOutcomeMappingForm,
    build_grade_formset,
)
from assessments.models import Assessment
from assessments.program_outcome_scoring import calculate_program_outcome_scores
from assessments.services import save_bulk_grades
from assessments.scoring import calculate_learning_outcome_scores


class AssessmentManagerRequiredMixin(DepartmentHeadRequiredMixin):
    """Allow Department Heads and assigned instructors into assessment workflows."""

    def test_func(self):
        user = self.request.user
        return has_role(user, ROLE_DEPARTMENT_HEAD) or has_role(user, ROLE_INSTRUCTOR)


class AssessmentListView(AssessmentManagerRequiredMixin, TemplateView):
    template_name = "assessments/assessment_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessments"] = Assessment.objects.filter(
            offering__in=manageable_offerings(self.request.user)
        ).select_related("offering__course", "offering__term")
        context["offerings"] = manageable_offerings(self.request.user).select_related("course", "term")
        return context


class AssessmentCreateView(AssessmentManagerRequiredMixin, CreateView):
    template_name = "assessments/assessment_form.html"
    form_class = AssessmentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("assessments:detail", kwargs={"pk": self.object.pk})


class ManagedAssessmentMixin(AssessmentManagerRequiredMixin):
    assessment = None

    def get_assessment(self):
        if self.assessment is None:
            self.assessment = get_object_or_404(
                Assessment.objects.select_related("offering__course", "offering__term"), pk=self.kwargs["pk"]
            )
            if not can_manage_assessment(self.request.user, self.assessment):
                raise PermissionDenied
        return self.assessment


class AssessmentDetailView(ManagedAssessmentMixin, TemplateView):
    template_name = "assessments/assessment_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.get_assessment()
        context.update(
            {
                "assessment": assessment,
                "mappings": assessment.learning_outcome_mappings.select_related("learning_outcome"),
                "grade_count": assessment.grades.count(),
            }
        )
        return context


class AssessmentMappingCreateView(ManagedAssessmentMixin, CreateView):
    template_name = "assessments/mapping_form.html"
    form_class = AssessmentLearningOutcomeMappingForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["assessment"] = self.get_assessment()
        return kwargs

    def get_success_url(self):
        return reverse("assessments:detail", kwargs={"pk": self.get_assessment().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment"] = self.get_assessment()
        return context


class GradeEntryView(ManagedAssessmentMixin, View):
    template_name = "assessments/grade_entry.html"

    def get(self, request, *args, **kwargs):
        assessment = self.get_assessment()
        return self.render_formset(request, assessment, build_grade_formset(assessment))

    def post(self, request, *args, **kwargs):
        assessment = self.get_assessment()
        formset = build_grade_formset(assessment, data=request.POST)
        if formset.is_valid():
            save_bulk_grades(assessment, [form.cleaned_data for form in formset])
            messages.success(request, "Grades saved.")
            return redirect("assessments:grades", pk=assessment.pk)
        return self.render_formset(request, assessment, formset)

    def render_formset(self, request, assessment, formset):
        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {"assessment": assessment, "formset": formset},
        )


class OutcomeScoreView(AssessmentManagerRequiredMixin, TemplateView):
    template_name = "assessments/outcome_scores.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offering = get_object_or_404(
            CourseOffering.objects.select_related("course", "term"), pk=self.kwargs["pk"]
        )
        if not can_manage_offering(self.request.user, offering):
            raise PermissionDenied
        learning_outcomes, student_scores = calculate_learning_outcome_scores(offering)
        context.update(
            {
                "offering": offering,
                "learning_outcomes": learning_outcomes,
                "student_scores": student_scores,
            }
        )
        return context


class ProgramOutcomeScoreView(AssessmentManagerRequiredMixin, TemplateView):
    template_name = "assessments/program_outcome_scores.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offering = get_object_or_404(
            CourseOffering.objects.select_related("course__program", "term"), pk=self.kwargs["pk"]
        )
        if not can_manage_offering(self.request.user, offering):
            raise PermissionDenied
        program_outcomes, student_scores = calculate_program_outcome_scores(offering)
        context.update(
            {
                "offering": offering,
                "program_outcomes": program_outcomes,
                "student_scores": student_scores,
            }
        )
        return context
