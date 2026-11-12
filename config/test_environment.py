import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from config.environment import load_environment_file


class LoadEnvironmentFileTests(TestCase):
    def setUp(self):
        self.key = "STRAITAI_TEST_ENVIRONMENT_VALUE"
        self.original_value = os.environ.pop(self.key, None)

    def tearDown(self):
        os.environ.pop(self.key, None)
        if self.original_value is not None:
            os.environ[self.key] = self.original_value

    def test_loads_unset_values_and_ignores_comments(self):
        environment_file = Path(".env")
        contents = "# Local settings\nSTRAITAI_TEST_ENVIRONMENT_VALUE='loaded value'\n"

        with (
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "read_text", return_value=contents),
        ):
            load_environment_file(environment_file)

        self.assertEqual(os.environ[self.key], "loaded value")

    def test_does_not_override_existing_environment_values(self):
        os.environ[self.key] = "process value"
        environment_file = Path(".env")

        with (
            patch.object(Path, "is_file", return_value=True),
            patch.object(
                Path,
                "read_text",
                return_value="STRAITAI_TEST_ENVIRONMENT_VALUE=file value\n",
            ),
        ):
            load_environment_file(environment_file)

        self.assertEqual(os.environ[self.key], "process value")
