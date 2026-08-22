"""
dj-stripe PaymentIntent Model Tests.
"""

from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase

from djstripe.models import Customer, PaymentIntent
from djstripe.settings import djstripe_settings

from . import FAKE_CUSTOMER, FAKE_PAYMENT_INTENT_I
from .conftest import CreateAccountMixin
from .stripe_world import mock_stripe_world


class PaymentIntentCreateTest(CreateAccountMixin, TestCase):
    def setUp(self):
        with mock_stripe_world():
            self.customer = Customer.sync_from_stripe_data(deepcopy(FAKE_CUSTOMER))

    @patch(
        "stripe.PaymentIntent.create",
        return_value=deepcopy(FAKE_PAYMENT_INTENT_I),
        autospec=True,
    )
    def test_create(self, create_mock):
        with mock_stripe_world():
            payment_intent = PaymentIntent.create(
                amount=2000, currency="usd", customer=self.customer
            )

        create_mock.assert_called_once_with(
            api_key=djstripe_settings.STRIPE_SECRET_KEY,
            stripe_version=djstripe_settings.STRIPE_API_VERSION,
            amount=2000,
            currency="usd",
            customer=self.customer.id,
        )
        assert isinstance(payment_intent, PaymentIntent)
        assert payment_intent.id == FAKE_PAYMENT_INTENT_I["id"]
        assert payment_intent.customer == self.customer
        assert PaymentIntent.objects.filter(id=payment_intent.id).exists()

    @patch(
        "stripe.PaymentIntent.create",
        return_value=deepcopy(FAKE_PAYMENT_INTENT_I),
        autospec=True,
    )
    def test_create_passes_through_plain_kwargs(self, create_mock):
        with mock_stripe_world():
            PaymentIntent.create(
                amount=2000,
                currency="usd",
                customer=self.customer.id,
                metadata={"order": "1"},
            )

        kwargs = create_mock.call_args.kwargs
        assert kwargs["customer"] == self.customer.id
        assert kwargs["metadata"] == {"order": "1"}
