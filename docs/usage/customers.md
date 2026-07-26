# Working with customers

The [`Customer`][djstripe.models.core.Customer] model is the hub of most dj-stripe
integrations. It links one of your **subscribers** (by default your
`AUTH_USER_MODEL`, configurable via
[`DJSTRIPE_SUBSCRIBER_MODEL`](../settings.md#djstripe_subscriber_model)) to a Stripe
customer, and exposes helper methods for the common billing workflows.

## Getting a customer

Use [`Customer.get_or_create`][djstripe.models.core.Customer.get_or_create] to fetch
or create the Stripe customer for a subscriber. This is the usual entry point:

```python
from djstripe.models import Customer

customer, created = Customer.get_or_create(subscriber=request.user)
```

The first call creates the customer in Stripe and stores it locally; subsequent
calls return the existing record.

## Helper methods

`Customer` wraps the most common operations so you rarely need to call the Stripe
API directly:

| Method | Purpose |
| --- | --- |
| [`subscribe()`][djstripe.models.core.Customer.subscribe] | Subscribe the customer to one or more prices. See [Subscribing customers](subscribing_customers.md). |
| [`charge()`][djstripe.models.core.Customer.charge] | Create a one-off charge. See [Creating individual charges](creating_individual_charges.md). |
| [`add_payment_method()`][djstripe.models.core.Customer.add_payment_method] | Attach a payment method. See [Adding a payment method](add_payment_method_to_customer.md). |
| [`add_invoice_item()`][djstripe.models.core.Customer.add_invoice_item] | Add a one-off line item to the customer's next invoice. |
| [`add_coupon()`][djstripe.models.core.Customer.add_coupon] | Apply a coupon to the customer. |
| [`send_invoice()`][djstripe.models.core.Customer.send_invoice] | Create and send an invoice. |
| [`upcoming_invoice()`][djstripe.models.core.Customer.upcoming_invoice] | Preview the customer's next invoice. |
| [`purge()`][djstripe.models.core.Customer.purge] | Delete the customer in Stripe and detach it locally. |

## Accessing subscriptions

Because Stripe data is mirrored into Django models, you query a customer's related
objects through the ORM:

```python
customer.subscriptions.all()
customer.invoices.all()
customer.charges.all()
```

Subscription status does not by itself determine whether a customer should have
access to your application. For example, some applications allow access while a
payment is being retried and the subscription is `past_due`, while others revoke
it immediately. Define that policy in your application by explicitly selecting
the statuses you accept:

```python
from djstripe.enums import SubscriptionStatus

SERVICE_STATUSES = {
    SubscriptionStatus.trialing,
    SubscriptionStatus.active,
    SubscriptionStatus.past_due,
}

service_subscriptions = (
    customer.subscriptions.with_status(*SERVICE_STATUSES).period_current()
)

has_access = service_subscriptions.exists()
has_product_access = service_subscriptions.for_product(product).exists()
```

The subscription queryset filters are composable:

| Filter | Purpose |
| --- | --- |
| `with_status(*statuses)` | Select one or more explicit Stripe statuses. |
| `active()`, `trialing()`, `past_due()`, `canceled()`, `incomplete()` | Select a single Stripe status. |
| `period_current(at=None)` | Select subscriptions whose billing period or trial contains a point in time. |
| `scheduled_for_cancellation()` | Select subscriptions set to cancel at the end of their period. |
| `for_product(product)` | Select subscriptions containing a price for a product or product ID. |

These filters are available from both `Subscription.objects` and the
`customer.subscriptions` reverse relation. Use
[`Subscription.is_period_current()`][djstripe.models.billing.Subscription.is_period_current]
or
[`Subscription.is_scheduled_for_cancellation()`][djstripe.models.billing.Subscription.is_scheduled_for_cancellation]
when working with one subscription instance.

See the [`Customer` API reference][djstripe.models.core.Customer] for the full list
of methods, properties and relations.
