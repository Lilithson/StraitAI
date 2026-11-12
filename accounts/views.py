from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from accounts.forms import EnrollmentForm, StudentCreationForm
from accounts.mixins import DepartmentHeadRequiredMixin
from accounts.models import Enrollment, StudentProfile


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
