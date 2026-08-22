# Managing subscriptions and payment methods

All of the methods below call the Stripe API and sync the result back into the
local database, so the returned object is current without waiting for a webhook.

## Changing a subscription

[`Subscription.update()`][djstripe.models.billing.Subscription.update] accepts any
argument the Stripe
[update subscription](https://stripe.com/docs/api/subscriptions/update) endpoint
takes:

```python
subscription = customer.subscriptions.active().first()

# Change quantity or price on the existing item
subscription.update(
    items=[{"id": subscription.items.first().id, "price": new_price.id}],
    proration_behavior="create_prorations",
)

# Pause collection
subscription.update(pause_collection={"behavior": "void"})
```

## Cancelling

[`Subscription.cancel()`][djstripe.models.billing.Subscription.cancel] cancels
immediately by default. Pass `at_period_end=True` to keep the subscription active
until the current period ends:

```python
subscription.cancel(at_period_end=True)
```

Subscriptions scheduled this way are returned by
`Subscription.objects.scheduled_for_cancellation()`. To undo before the period
ends, call `subscription.update(cancel_at_period_end=False)`.

## Extending

[`Subscription.extend(delta)`][djstripe.models.billing.Subscription.extend] pushes
the next billing date out by a positive `timedelta`, for out-of-band payment such
as gift cards:

```python
from datetime import timedelta

subscription.extend(timedelta(days=30))
```

**Warning:** Extension works by moving `trial_end`, so Stripe sets the
subscription status to `trialing` until the new date.

## Payment methods

Attach a payment method collected in the browser with
[`Customer.add_payment_method()`][djstripe.models.core.Customer.add_payment_method];
it becomes the default unless you pass `set_default=False`. See
[Adding a payment method](add_payment_method_to_customer.md).

To change the default later, update the customer in Stripe and sync:

```python
import stripe
from djstripe.models import Customer

stripe_customer = stripe.Customer.modify(
    customer.id,
    invoice_settings={"default_payment_method": payment_method.id},
    api_key=customer.default_api_key,
)
Customer.sync_from_stripe_data(stripe_customer)
```

To remove a payment method, call
[`PaymentMethod.detach()`][djstripe.models.payment_methods.PaymentMethod.detach]:

```python
payment_method = customer.payment_methods.get(id="pm_...")
payment_method.detach()
```

A detached payment method can no longer be charged and is unlinked from the
customer locally.
