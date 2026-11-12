from decimal import Decimal

from django import forms
from django.forms import formset_factory

from accounts.models import Enrollment
from assessments.access import manageable_offerings
from assessments.models import Assessment, AssessmentLearningOutcomeMapping, Grade


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ("offering", "title", "kind", "max_score", "due_date")
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["offering"].queryset = manageable_offerings(user).select_related("course", "term")


class AssessmentLearningOutcomeMappingForm(forms.ModelForm):
    class Meta:
        model = AssessmentLearningOutcomeMapping
        fields = ("learning_outcome", "weight")

    def __init__(self, *args, assessment, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.assessment = assessment
        self.fields["learning_outcome"].queryset = assessment.offering.course.learning_outcomes.all()


class GradeEntryForm(forms.Form):
    enrollment_id = forms.IntegerField(widget=forms.HiddenInput)
    score = forms.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal("0"), required=False)

    def __init__(self, *args, assessment, enrollment_lookup, **kwargs):
        super().__init__(*args, **kwargs)
        self.assessment = assessment
        self.enrollment_lookup = enrollment_lookup
        enrollment_id = self.initial.get("enrollment_id")
        self.enrollment = enrollment_lookup.get(enrollment_id)

    def clean(self):
        cleaned_data = super().clean()
        enrollment_id = cleaned_data.get("enrollment_id")
        if enrollment_id not in self.enrollment_lookup:
            raise forms.ValidationError("This student is not eligible for this assessment.")
        score = cleaned_data.get("score")
        if score is not None and score > self.assessment.max_score:
            self.add_error("score", f"Score cannot exceed {self.assessment.max_score}.")
        return cleaned_data


GradeEntryFormSet = formset_factory(GradeEntryForm, extra=0)


def build_grade_formset(assessment, data=None):
    enrollments = list(
        Enrollment.objects.filter(
            offering=assessment.offering, status=Enrollment.Status.ENROLLED
        ).select_related("student__user")
    )
    enrollment_lookup = {enrollment.pk: enrollment for enrollment in enrollments}
    existing_scores = dict(
        Grade.objects.filter(assessment=assessment).values_list("enrollment_id", "score")
    )
    initial = [
        {"enrollment_id": enrollment.pk, "score": existing_scores.get(enrollment.pk)}
        for enrollment in enrollments
    ]
    return GradeEntryFormSet(
        data=data,
        initial=initial,
        form_kwargs={"assessment": assessment, "enrollment_lookup": enrollment_lookup},
    )
