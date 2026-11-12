from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("students/", views.StudentManagementView.as_view(), name="students"),
    path("students/add/", views.StudentCreateView.as_view(), name="student-add"),
    path("enrollments/add/", views.EnrollmentCreateView.as_view(), name="enrollment-add"),
]
