"""Central role names and server-side authorization helpers."""

ROLE_STUDENT = "Student"
ROLE_INSTRUCTOR = "Instructor"
ROLE_DEPARTMENT_HEAD = "Department Head"
DEFAULT_ROLE_NAMES = (ROLE_STUDENT, ROLE_INSTRUCTOR, ROLE_DEPARTMENT_HEAD)


def has_role(user, role_name):
    """Return whether an authenticated user has a named StraitAI role."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.groups.filter(name=role_name).exists())
    )


def can_manage_offering(user, offering):
    """Return whether a user may manage data for a course offering."""
    if has_role(user, ROLE_DEPARTMENT_HEAD):
        return True

    return has_role(user, ROLE_INSTRUCTOR) and offering.instructors.filter(pk=user.pk).exists()
