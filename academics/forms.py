from django import forms

from academics.models import AcademicTerm, Course, CourseOffering, LearningOutcome, Program, ProgramOutcome


class AcademicTermForm(forms.ModelForm):
    class Meta:
        model = AcademicTerm
        fields = ("year", "season")


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ("code", "name")


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("program", "code", "title", "credit_hours")


class ProgramOutcomeForm(forms.ModelForm):
    class Meta:
        model = ProgramOutcome
        fields = ("program", "code", "description", "is_active")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class LearningOutcomeForm(forms.ModelForm):
    class Meta:
        model = LearningOutcome
        fields = ("course", "code", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class CourseOfferingForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = ("course", "term", "section", "instructors")
        widgets = {"instructors": forms.CheckboxSelectMultiple}
