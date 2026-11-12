from django.db.models import QuerySet

from accounts.roles import ROLE_DEPARTMENT_HEAD, ROLE_INSTRUCTOR, has_role
from academics.models import CourseOffering


def manageable_offerings(user) -> QuerySet[CourseOffering]:
    if has_role(user, ROLE_DEPARTMENT_HEAD):
        return CourseOffering.objects.all()
    if has_role(user, ROLE_INSTRUCTOR):
        return CourseOffering.objects.filter(instructors=user)
    return CourseOffering.objects.none()


def can_manage_assessment(user, assessment) -> bool:
    return manageable_offerings(user).filter(pk=assessment.offering_id).exists()
