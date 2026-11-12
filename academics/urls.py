from django.urls import path

from academics import views

app_name = "academics"

urlpatterns = [
    path("setup/", views.SetupOverviewView.as_view(), name="setup"),
    path("terms/add/", views.AcademicTermCreateView.as_view(), name="term-add"),
    path("programs/add/", views.ProgramCreateView.as_view(), name="program-add"),
    path("courses/add/", views.CourseCreateView.as_view(), name="course-add"),
    path("program-outcomes/add/", views.ProgramOutcomeCreateView.as_view(), name="program-outcome-add"),
    path("learning-outcomes/add/", views.LearningOutcomeCreateView.as_view(), name="learning-outcome-add"),
    path("offerings/add/", views.CourseOfferingCreateView.as_view(), name="offering-add"),
]
