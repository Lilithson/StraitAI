from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from accounts.roles import ROLE_DEPARTMENT_HEAD, has_role
from academics.forms import AcademicTermForm, CourseForm, CourseOfferingForm, LearningOutcomeForm, ProgramForm, ProgramOutcomeForm
from academics.models import AcademicTerm, Course, CourseOffering, LearningOutcome, Program, ProgramOutcome


class DepartmentHeadRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow academic setup only to superusers and Department Heads."""

    def test_func(self):
        return has_role(self.request.user, ROLE_DEPARTMENT_HEAD)


class SetupOverviewView(DepartmentHeadRequiredMixin, TemplateView):
    template_name = "academics/setup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "program_count": Program.objects.count(),
                "term_count": AcademicTerm.objects.count(),
                "course_count": Course.objects.count(),
                "outcome_count": ProgramOutcome.objects.count(),
                "learning_outcome_count": LearningOutcome.objects.count(),
                "offering_count": CourseOffering.objects.count(),
                "programs": Program.objects.all(),
                "terms": AcademicTerm.objects.all(),
                "courses": Course.objects.select_related("program"),
                "program_outcomes": ProgramOutcome.objects.select_related("program"),
                "learning_outcomes": LearningOutcome.objects.select_related("course"),
                "offerings": CourseOffering.objects.select_related("course", "term"),
            }
        )
        return context


class SetupCreateView(DepartmentHeadRequiredMixin, CreateView):
    template_name = "academics/setup_form.html"
    success_url = reverse_lazy("academics:setup")
    page_title = "Add record"
    submit_label = "Save"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": self.page_title, "submit_label": self.submit_label})
        return context


class ProgramCreateView(SetupCreateView):
    form_class = ProgramForm
    page_title = "Add program"
    submit_label = "Create program"


class AcademicTermCreateView(SetupCreateView):
    form_class = AcademicTermForm
    page_title = "Add academic term"
    submit_label = "Create term"


class CourseCreateView(SetupCreateView):
    form_class = CourseForm
    page_title = "Add course"
    submit_label = "Create course"


class ProgramOutcomeCreateView(SetupCreateView):
    form_class = ProgramOutcomeForm
    page_title = "Add program outcome"
    submit_label = "Create program outcome"


class LearningOutcomeCreateView(SetupCreateView):
    form_class = LearningOutcomeForm
    page_title = "Add learning outcome"
    submit_label = "Create learning outcome"


class CourseOfferingCreateView(SetupCreateView):
    form_class = CourseOfferingForm
    page_title = "Add course offering"
    submit_label = "Create offering"
