from django.contrib import admin

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


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ("year", "season")
    list_filter = ("season",)
    ordering = ("-year", "season")


@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ("code", "program", "is_active")
    list_filter = ("program", "is_active")
    search_fields = ("code", "description")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "program", "credit_hours")
    list_filter = ("program",)
    search_fields = ("code", "title")


@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ("course", "term", "section")
    list_filter = ("term", "course__program")
    search_fields = ("course__code", "course__title", "section")
    filter_horizontal = ("instructors",)


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ("code", "course")
    list_filter = ("course__program",)
    search_fields = ("code", "description", "course__code")


@admin.register(LearningOutcomeProgramOutcomeMapping)
class LearningOutcomeProgramOutcomeMappingAdmin(admin.ModelAdmin):
    list_display = ("learning_outcome", "program_outcome", "weight")
    list_filter = ("program_outcome__program",)


@admin.register(CourseProgramOutcomeMapping)
class CourseProgramOutcomeMappingAdmin(admin.ModelAdmin):
    list_display = ("course", "program_outcome", "weight")
    list_filter = ("course__program",)
