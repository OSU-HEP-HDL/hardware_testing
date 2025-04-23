"""
Module for managing base settings for itkdb

!!! note "Changed in version 0.6.0"
    - renamed `ITKDB_SITE_URL` to `ITKDB_API_URL`
"""

from __future__ import annotations

SIMPLE_SETTINGS = {"OVERRIDE_BY_ENV": True}
ITKDB_ACCESS_CODE1 = ""
ITKDB_ACCESS_CODE2 = ""
ITKDB_AUDREYTWO_API_KEY = ""
ITKDB_ACCESS_SCOPE = "openid https://itkpd-test.unicorncollege.cz"
ITKDB_ACCESS_AUDIENCE = "https://itkpd-test.unicorncollege.cz"
ITKDB_AUTH_URL = "https://uuidentity.plus4u.net/uu-oidc-maing02/bb977a99f4cc4c37a2afce3fd599d0a7/oidc/"
ITKDB_API_URL = "https://itkpd-test.unicorncollege.cz/"
ITKDB_CASSETTE_LIBRARY_DIR = "tests/integration/cassettes"
ITKDB_LEEWAY = 2
