"""Tests the react_locales utils for Marsha core app."""
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings

from marsha.core.utils.react_locales_utils import react_locale


class ReactLocaleUtils(TestCase):
    """Unit test suite to validate the behavior of the `react_locale`."""

    @override_settings(REACT_LOCALES=["en_US", "fr_CA", "fr_FR", "es_ES"])
    def test_utils_react_locale_canada_first(self):
        """Languages should return the first matching React locale (Canada comes before France)."""
        # Full languages
        self.assertEqual(react_locale("fr-FR"), "fr_FR")
        self.assertEqual(react_locale("fr-CA"), "fr_CA")

        # Simple languages
        self.assertEqual(react_locale("en"), "en_US")
        self.assertEqual(react_locale("es"), "es_ES")
        self.assertEqual(react_locale("fr"), "fr_CA")

    @override_settings(REACT_LOCALES=["en_US", "fr_FR", "fr_CA", "es_ES"])
    def test_utils_react_locale_france_first(self):
        """Languages should return the first matching React locale (France comes before Canada)."""
        self.assertEqual(react_locale("en"), "en_US")
        self.assertEqual(react_locale("es"), "es_ES")
        self.assertEqual(react_locale("fr"), "fr_FR")

    @override_settings(REACT_LOCALES=["en_US", "fr_CA", "fr_FR", "es_ES"])
    def test_utils_react_locale_absent(self):
        """An exception should be raised if the language does not correspond to a React locale."""
        with self.assertRaises(ImproperlyConfigured):
            react_locale("fr-BE")

        with self.assertRaises(ImproperlyConfigured):
            react_locale("it")
