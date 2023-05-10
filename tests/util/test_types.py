from itertools import product
from urllib.parse import ParseResult, urlparse

import pytest
from rdflib import URIRef

from vocata.util.types import coerce_uris


@pytest.mark.parametrize("arg_t,ann", list(product((str, URIRef, ParseResult), repeat=2)))
def test_coerce_uris(arg_t, ann):
    test_uri = "https://example.com/test/foo#bar"
    test_int = 23
    test_bool = True

    if arg_t == ParseResult:
        test_arg = urlparse(test_uri)
    else:
        test_arg = arg_t(test_uri)

    @coerce_uris
    def _test_func(a: ann, b: int, c: bool = test_bool):
        return a, b, c

    a, b, c = _test_func(test_arg, test_int)

    assert isinstance(a, ann)
    if ann == ParseResult:
        assert a.geturl() == test_uri
    else:
        assert str(a) == test_uri

    assert b == test_int
    assert c == test_bool
