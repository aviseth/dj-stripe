from unittest.mock import patch

from django.core import checks
from django.core.management import call_command
from django.db.utils import DatabaseError
from django.template.loader import get_template
from django.test import TestCase
from django.test.utils import override_settings

from djstripe.checks import check_webhook_endpoint_secrets_are_valid
from djstripe.models import WebhookEndpoint


class TestRunManagePyCheck(TestCase):
    @override_settings(
        STRIPE_TEST_SECRET_KEY="sk_test_foo",
        STRIPE_LIVE_SECRET_KEY="sk_live_foo",
        STRIPE_TEST_PUBLIC_KEY="pk_test_foo",
        STRIPE_LIVE_PUBLIC_KEY="pk_live_foo",
        STRIPE_LIVE_MODE=True,
    )
    def test_manage_py_check(self):
        call_command("check")

    def test_webhook_endpoint_admin_change_form_template_compiles(self):
        get_template("djstripe/admin/webhook_endpoint/change_form.html")


class TestSystemChecksDoNotTouchTheDatabase(TestCase):
    """
    Regression tests for #2005.

    dj-stripe's system checks used to query `WebhookEndpoint` on every
    management command, which opens a connection to the configured database.
    That breaks tooling which expects no open connections (e.g. django-extensions'
    `reset_db`). The checks that need the database are tagged `Tags.database`,
    which Django excludes from the default check run.
    """

    def test_default_check_run_makes_no_queries(self):
        with self.assertNumQueries(0):
            checks.run_checks()

    def test_database_tagged_checks_still_run(self):
        # The checks must not merely be silenced -- they still have to run
        # where database access is expected, e.g. `manage.py check --database`.
        WebhookEndpoint.objects.create(
            id="we_test_no_secret",
            secret="",
            enabled_events=["*"],
            stripe_data={"id": "we_test_no_secret", "object": "webhook_endpoint"},
        )

        messages = checks.run_checks(tags=[checks.Tags.database])

        assert "djstripe.W005" in {m.id for m in messages}

    def test_setting_checks_still_run_by_default(self):
        # Splitting the endpoint checks out must not take the non-database
        # setting validation with them.
        with override_settings(DJSTRIPE_WEBHOOK_VALIDATION="not-a-valid-option"):
            messages = checks.run_checks()

        assert "djstripe.C007" in {m.id for m in messages}

    @override_settings(DJSTRIPE_WEBHOOK_VALIDATION="verify_signature")
    def test_database_tagged_checks_survive_an_unavailable_database(self):
        # An unmigrated or unreachable database must degrade to "no messages"
        # rather than crashing the very `migrate` that would fix it.
        # Both managers are stubbed: the secrets check calls .all(), the
        # has-secret check calls .filter().
        manager = WebhookEndpoint.objects
        error = DatabaseError("no such table: djstripe_webhookendpoint")

        with (
            patch.object(manager, "all", side_effect=error),
            patch.object(manager, "filter", side_effect=error),
        ):
            messages = checks.run_checks(tags=[checks.Tags.database])

        assert messages == []

    @override_settings(DJSTRIPE_WEBHOOK_VALIDATION="retrieve_event")
    def test_endpoint_secret_check_skips_unless_verifying_signatures(self):
        # Secrets are only used for signature verification, so the check
        # short-circuits in any other mode -- without hitting the database.
        WebhookEndpoint.objects.create(
            id="we_test_retrieve_event",
            secret="",
            enabled_events=["*"],
            stripe_data={"id": "we_test_retrieve_event", "object": "webhook_endpoint"},
        )

        with self.assertNumQueries(0):
            assert check_webhook_endpoint_secrets_are_valid() == []
