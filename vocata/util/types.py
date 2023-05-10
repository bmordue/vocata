from functools import wraps
from inspect import signature
from typing import Callable
from urllib.parse import ParseResult, urlparse

from rdflib import URIRef
from rdflib.term import Node


def coerce_uris(func: Callable) -> Callable:
    """Coerce the relevant URI types into the expected one of each argument."""
    orig_ann = []
    for arg, ann in func.__annotations__.items():
        if arg != "return":
            orig_ann.append((arg, ann))

    @wraps(func)
    def _coerced(*args, **kwargs):
        # Map positional args into kwargs
        kwargs.update(signature(func).bind_partial(*args).arguments)

        for arg, ann in orig_ann:
            if ann not in (str, Node, URIRef, ParseResult):
                # Only touch arguments that are declared a supported type
                continue
            if type(kwargs[arg]) == ann:
                # Skip if argument already has correct type
                continue

            # First, coerce into string
            if type(kwargs[arg]) == str:
                s = kwargs[arg]
            elif type(kwargs[arg]) == ParseResult:
                s = kwargs[arg].geturl()
            elif type(kwargs[arg]) == URIRef:
                s = str(kwargs[arg])
            elif type(kwargs[arg]) == Node:
                raise TypeError(f"Generic Node passed as {arg} when URI was expected")

            # Second, traverse into target
            if ann == str:
                kwargs[arg] = s
            elif ann == ParseResult:
                kwargs[arg] = urlparse(s)
            elif ann in (Node, URIRef):
                kwargs[arg] = URIRef(s)

        # Finally, call original method
        return func(**kwargs)

    # Update annotations of wrapper function
    for arg in _coerced.__annotations__.keys():
        if _coerced.__annotations__[arg] in (str, Node, URIRef, ParseResult):
            _coerced.__annotations__[arg] = str | URIRef | ParseResult
        if _coerced.__annotations__[arg] == Node:
            _coerced.__annotations__[arg] |= Node

    return _coerced
