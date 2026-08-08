"""
dj-stripe - Django + Stripe Made Easy
"""

from importlib.metadata import version

from django.apps import AppConfig

__version__ = version("dj-stripe")


class DjstripeAppConfig(AppConfig):
    """
    An AppConfig for dj-stripe which loads system checks
    and event handlers once Django is ready.
    """

    name = "djstripe"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import stripe

        # Imported for their side effects: _stripe_compat patches StripeObject
        # for stripe v15+, while checks and event_handlers register themselves.
        from . import (  # noqa: F401
            _stripe_compat,
            checks,
            event_handlers,
        )

        # Set app info
        # https://stripe.com/docs/building-plugins#setappinfo
        stripe.set_app_info(
            "dj-stripe",
            version=__version__,
            url="https://github.com/dj-stripe/dj-stripe",
        )
