from django.test import SimpleTestCase
from django.urls import reverse


class HealthCheckTests(SimpleTestCase):
    def test_health_check_returns_ok_status(self):
        response = self.client.get(reverse("core:health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})

    def test_health_check_rejects_non_get_requests(self):
        response = self.client.post(reverse("core:health-check"))

        self.assertEqual(response.status_code, 405)


class HomePageTests(SimpleTestCase):
    def test_home_page_renders_the_mock_dashboard(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertContains(response, "StraitAI")
        self.assertContains(response, "Demo workspace")
