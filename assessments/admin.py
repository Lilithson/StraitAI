from django.contrib import admin

from assessments.models import Assessment, AssessmentLearningOutcomeMapping, Grade


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "offering", "max_score", "due_date")
    list_filter = ("kind", "offering__term", "offering__course")
    search_fields = ("title", "offering__course__code")


@admin.register(AssessmentLearningOutcomeMapping)
class AssessmentLearningOutcomeMappingAdmin(admin.ModelAdmin):
    list_display = ("assessment", "learning_outcome", "weight")
    list_filter = ("assessment__offering__course",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("assessment", "enrollment", "score", "recorded_at")
    list_filter = ("assessment__offering__term", "assessment__offering__course")
    search_fields = ("enrollment__student__student_number", "assessment__title")
