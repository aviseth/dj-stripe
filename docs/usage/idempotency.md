# Idempotency

Stripe accepts an
[idempotency key](https://stripe.com/docs/api/idempotent_requests) on write
requests so a retried request does not create a duplicate object.

## What dj-stripe does

dj-stripe generates a key when it creates a customer for a subscriber in
[`Customer.get_or_create()`][djstripe.models.core.Customer.get_or_create]. Keys
are stored in the [`IdempotencyKey`][djstripe.models.base.IdempotencyKey] model,
one per `(action, livemode)`, so a repeated attempt to create the same customer
reuses the same key and Stripe returns the original customer instead of a second
one.

Stripe honours a key for 24 hours. Remove expired rows with:

```bash
python manage.py djstripe_clear_expired_idempotency_keys
```

## Customising key generation

Set `DJSTRIPE_IDEMPOTENCY_KEY_CALLBACK` to a callable
`(object_type, action, livemode) -> str` to supply your own keys:

```python
DJSTRIPE_IDEMPOTENCY_KEY_CALLBACK = "myapp.billing.idempotency_key"
```

## Your own requests

Methods that accept `idempotency_key` (for example
[`Customer.add_coupon()`][djstripe.models.core.Customer.add_coupon]) pass it
through to Stripe. When you call the Stripe API directly, pass
`idempotency_key=` yourself, and keep your webhook handlers idempotent: Stripe
retries failed deliveries, so the same event can arrive more than once.
