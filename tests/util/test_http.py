from requests import Request

from vocata.util.http import HTTPSignatureAuth


def test_sign_verify(graph, actor, local_domain):
    headers = ["(request-target)", "host", "date", "digest"]
    data = {"summary": "Test Data"}

    auth = HTTPSignatureAuth(graph, headers, actor=actor)
    request = Request("POST", f"https://{local_domain}/test", json=data, auth=auth)

    prepared = request.prepare()
    assert "Signature" in prepared.headers

    # FIXME mock this correctly
    prepared.state = type("_State", tuple(), {"graph": graph})
    HTTPSignatureAuth.from_signed_request(prepared, pull=False).verify_request(prepared)
