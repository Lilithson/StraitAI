from django.contrib import admin

from accounts.models import Enrollment, StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student_number", "user", "program", "is_active")
    list_filter = ("program", "is_active")
    search_fields = ("student_number", "user__username", "user__first_name", "user__last_name")
    autocomplete_fields = ("user", "program")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "offering", "status", "enrolled_at")
    list_filter = ("status", "offering__term", "offering__course__program")
    search_fields = (
        "student__student_number",
        "student__user__username",
        "offering__course__code",
    )
    autocomplete_fields = ("student", "offering")
