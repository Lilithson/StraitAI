from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.RoleBasedLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("portal/", views.StudentPortalView.as_view(), name="student-portal"),
    path("students/", views.StudentManagementView.as_view(), name="students"),
    path("students/add/", views.StudentCreateView.as_view(), name="student-add"),
    path("enrollments/add/", views.EnrollmentCreateView.as_view(), name="enrollment-add"),
]
