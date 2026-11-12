from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.roles import ROLE_DEPARTMENT_HEAD, has_role


class DepartmentHeadRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow configuration work only to superusers and Department Heads."""

    def test_func(self):
        return has_role(self.request.user, ROLE_DEPARTMENT_HEAD)
