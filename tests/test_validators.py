import pytest
from django.core.exceptions import ValidationError

from backupgram.validators import validate_base_url


@pytest.mark.parametrize(
    "url",
    [
        "https://backup:8081",  # single-label docker service name
        "http://backup:8081",
        "https://10.0.0.5:8081",
        "https://db.example.com:8081/api",
        "http://localhost:8081",
    ],
)
def test_valid_urls(url):
    validate_base_url(url)  # must not raise


@pytest.mark.parametrize(
    "url",
    [
        "notaurl",
        "ftp://backup:8081",
        "https://",  # no host
        "backup:8081",  # no scheme
        "",
    ],
)
def test_invalid_urls(url):
    with pytest.raises(ValidationError):
        validate_base_url(url)
