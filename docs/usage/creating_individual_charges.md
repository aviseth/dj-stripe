# Creating individual charges

## Payment Intents (recommended)

Create a
[`PaymentIntent`](https://stripe.com/docs/payments/payment-intents) through the
Stripe API and sync it. This supports SCA and all payment method types:

```python
import stripe
from djstripe.models import PaymentIntent

intent = stripe.PaymentIntent.create(
    amount=1000,  # minor units: 10.00 USD
    currency="usd",
    customer=customer.id,
    payment_method=customer.default_payment_method.id,
    off_session=True,
    confirm=True,
    api_key=api_key,
)
PaymentIntent.sync_from_stripe_data(intent)
```

Collect the payment method in the browser first; see
[Integrating Stripe Elements](../stripe_elements_js.md). The resulting `Charge` is
synced through webhooks or when the intent is synced.

## `Customer.charge()` (legacy Charges API)

[`Customer.charge()`][djstripe.models.core.Customer.charge] wraps the older
[Charges API](https://stripe.com/docs/api/charges/create). It takes a `Decimal`
amount in major units and charges the customer's default source:

```python
from decimal import Decimal

customer.charge(Decimal("10.00"), currency="usd")
```

This does not handle authentication challenges such as 3D Secure and can fail
where SCA applies.
