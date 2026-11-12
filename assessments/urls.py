from django.urls import path

from assessments import views

app_name = "assessments"

urlpatterns = [
    path("", views.AssessmentListView.as_view(), name="list"),
    path("add/", views.AssessmentCreateView.as_view(), name="add"),
    path("<int:pk>/", views.AssessmentDetailView.as_view(), name="detail"),
    path("<int:pk>/mappings/add/", views.AssessmentMappingCreateView.as_view(), name="mapping-add"),
    path("<int:pk>/grades/", views.GradeEntryView.as_view(), name="grades"),
]
