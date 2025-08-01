from rfc3986 import uri_reference
from rfc3986.validators import Validator


def is_valid_url(url: str, *, require_scheme: bool = True) -> bool:
    try:
        uri = uri_reference(url).normalize()

        # Use the new Validator API
        validator = Validator()

        # Special handling for certain schemes that don't require host
        if uri.scheme in ("mailto", "data", "file"):
            # These schemes have their own validation rules
            if require_scheme:
                validator = validator.require_presence_of("scheme")
        else:
            # For typical URLs (http, https, ftp, etc.), require host
            if require_scheme:
                validator = validator.require_presence_of("scheme", "host")
            else:
                validator = validator.require_presence_of("host")

        # Check all components
        validator = validator.check_validity_of("scheme", "userinfo", "host", "port", "path", "query", "fragment")

        validator.validate(uri)
        return True
    except Exception:
        return False
