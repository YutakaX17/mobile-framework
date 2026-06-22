from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings import dev as dev_settings
from config.settings.database import build_postgres_database_config
from config.settings.worker import build_worker_config


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


class WorkerSettingsTests(SimpleTestCase):
    def test_worker_defaults_are_safe_for_local_development(self):
        config = build_worker_config(env={})

        self.assertEqual(config["BACKEND"], "sync")
        self.assertEqual(config["BROKER_URL"], "redis://localhost:6379/0")
        self.assertEqual(config["QUEUES"], ["default"])
        self.assertEqual(config["CONCURRENCY"], 1)
        self.assertEqual(config["POLL_INTERVAL_SECONDS"], 5)

    def test_worker_environment_overrides_are_supported(self):
        config = build_worker_config(
            env={
                "WORKER_BACKEND": "redis",
                "WORKER_BROKER_URL": "redis://redis:6379/1",
                "WORKER_QUEUES": "default,packages,sync",
                "WORKER_CONCURRENCY": "4",
                "WORKER_POLL_INTERVAL_SECONDS": "10",
            }
        )

        self.assertEqual(config["BACKEND"], "redis")
        self.assertEqual(config["BROKER_URL"], "redis://redis:6379/1")
        self.assertEqual(config["QUEUES"], ["default", "packages", "sync"])
        self.assertEqual(config["CONCURRENCY"], 4)
        self.assertEqual(config["POLL_INTERVAL_SECONDS"], 10)

    def test_worker_settings_reject_invalid_backend(self):
        with self.assertRaises(ImproperlyConfigured):
            build_worker_config(env={"WORKER_BACKEND": "unknown"})

    def test_worker_settings_reject_invalid_numeric_values(self):
        with self.assertRaises(ImproperlyConfigured):
            build_worker_config(env={"WORKER_CONCURRENCY": "0"})

        with self.assertRaises(ImproperlyConfigured):
            build_worker_config(env={"WORKER_POLL_INTERVAL_SECONDS": "not-a-number"})

    def test_worker_settings_require_at_least_one_queue(self):
        with self.assertRaises(ImproperlyConfigured):
            build_worker_config(env={"WORKER_QUEUES": " , "})


class DevelopmentSettingsTests(SimpleTestCase):
    def test_development_settings_trust_vite_admin_origins(self):
        self.assertIn("http://localhost:5173", dev_settings.CSRF_TRUSTED_ORIGINS)
        self.assertIn("http://127.0.0.1:5173", dev_settings.CSRF_TRUSTED_ORIGINS)
