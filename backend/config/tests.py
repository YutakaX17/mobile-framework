from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings.database import build_postgres_database_config


class PostgresDatabaseSettingsTests(SimpleTestCase):
    def test_required_postgres_settings_require_explicit_credentials(self):
        with self.assertRaises(ImproperlyConfigured):
            build_postgres_database_config(env={}, required=True)

    def test_development_defaults_match_compose_postgres(self):
        config = build_postgres_database_config(env={}, required=False)

        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(config["NAME"], "mobile_framework")
        self.assertEqual(config["USER"], "mobile_framework")
        self.assertEqual(config["PASSWORD"], "mobile_framework")
        self.assertEqual(config["HOST"], "localhost")
        self.assertEqual(config["PORT"], "5432")
        self.assertEqual(config["CONN_MAX_AGE"], 60)

    def test_environment_overrides_postgres_settings(self):
        config = build_postgres_database_config(
            env={
                "POSTGRES_DB": "custom_db",
                "POSTGRES_USER": "custom_user",
                "POSTGRES_PASSWORD": "secret",
                "POSTGRES_HOST": "postgres",
                "POSTGRES_PORT": "15432",
                "POSTGRES_CONN_MAX_AGE": "120",
                "POSTGRES_SSLMODE": "require",
            },
            required=True,
        )

        self.assertEqual(config["NAME"], "custom_db")
        self.assertEqual(config["USER"], "custom_user")
        self.assertEqual(config["PASSWORD"], "secret")
        self.assertEqual(config["HOST"], "postgres")
        self.assertEqual(config["PORT"], "15432")
        self.assertEqual(config["CONN_MAX_AGE"], 120)
        self.assertEqual(config["OPTIONS"], {"sslmode": "require"})

    def test_invalid_connection_max_age_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            build_postgres_database_config(env={"POSTGRES_CONN_MAX_AGE": "not-a-number"}, required=False)
