from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.db import transaction

from accounts.models import Enrollment, StudentProfile
from accounts.roles import ROLE_STUDENT
from academics.models import Program


class StudentCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    student_number = forms.CharField(max_length=32)
    program = forms.ModelChoiceField(queryset=Program.objects.all())

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")

    def clean_student_number(self):
        student_number = self.cleaned_data["student_number"]
        if StudentProfile.objects.filter(student_number=student_number).exists():
            raise forms.ValidationError("A student with this student number already exists.")
        return student_number

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            student_group, _ = Group.objects.get_or_create(name=ROLE_STUDENT)
            user.groups.add(student_group)
            return StudentProfile.objects.create(
                user=user,
                program=self.cleaned_data["program"],
                student_number=self.cleaned_data["student_number"],
            )
        return user


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ("student", "offering", "status")
