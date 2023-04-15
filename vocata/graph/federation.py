from importlib.metadata import metadata
from pprint import pformat

from requests import Response, Session
from requests.exceptions import JSONDecodeError

from ..util.http import HTTPSignatureAuth
from .authz import HAS_ACTOR, HAS_TRANSIENT_AUDIENCE, HAS_TRANSIENT_INBOXES, PUBLIC_ACTOR

CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class ActivityPubFederationMixin:
    _http_session: Session | None = None

    @property
    def _user_agent(self):
        meta = metadata("Vocata")
        return f"{meta['Name']}/{meta['Version']}"

    @property
    def http_session(self) -> Session:
        if self._http_session is None:
            self._logger.debug("Creating new HTTP client session")
            self._http_session = Session()
            self._http_session.headers = {
                "User-Agent": self._user_agent,
                "Accept": ", ".join(
                    [CONTENT_TYPE, "application/activity+json;q=0.9", "application/json;q=0.8"]
                ),
            }
        return self._http_session

    def _request(self, method: str, target: str, actor: str, data: dict | None = None) -> Response:
        if method not in ["GET", "POST"]:
            raise ValueError("Only GET and POST are valid HTTP methods for ActivityPub")

        self._logger.debug("Preparing new %s request to %s as %s", method, target, actor)

        headers = {}
        auth = None
        sign_headers = ["(request-target)", "host", "date"]
        if method == "POST":
            headers["Content-Type"] = CONTENT_TYPE
            sign_headers.append("digest")
        if actor != PUBLIC_ACTOR:
            auth = HTTPSignatureAuth(self, sign_headers, actor=actor)
            self._logger.debug("Enabled HTTP signatures for request")

        res = self.http_session.request(method, target, headers=headers, json=data, auth=auth)
        if res.status_code >= 400:
            try:
                error = res.json()
                self._logger.error("Request failed with error: %s", pformat(error))
            except JSONDecodeError:
                error = res.text
                self._logger.error("Request failed with error: %s", error)

        return res

    def pull(self, subject: str, actor: str = PUBLIC_ACTOR) -> tuple[bool, Response]:
        # FIXME distinguish between local and remote
        self._logger.info("Pulling %s from remote", subject)
        # FIXME validate URL
        response = self._request("GET", subject, actor)

        if response.status_code == 200:
            self._logger.debug("Successfully pulled %s", subject)
            self.add_jsonld(response.json())
        else:
            self._logger.error("Error pulling %s", subject)

        return response.status_code < 400, response

    def push_to(self, target: str, subject: str, actor: str) -> tuple[bool, Response]:
        self._logger.info("Pushing %s to remote %s", subject, target)
        # FIXME do we really want to retrieve as `actor` here?
        data = self.activitystream_cbd(subject, actor).to_activitystream(subject)
        if not data:
            # FIXME do we want to use this for re-pushing as well?
            #  in that case, we should pull first
            raise KeyError(f"{subject} is unknown")

        # FIXME test for locally owned targets here
        response = self._request("POST", target, actor, data)

        if response.status_code < 400:
            self._logger.debug("Successfully pushed %s to %s", subject, target)
        else:
            self._logger.error("Failed to push %s to %s", subject, target)

        return response.status_code < 400, response

    def get_all_targets(self, subject: str, actor: str = PUBLIC_ACTOR) -> set[str]:
        # FIXME we need to resolve for an actor!
        self._logger.debug("Resolving inboxes for audience of %s", subject)

        # FIXME enable once we can distinguish local and remote
        # self.pull(subject)

        audience = set()
        for _ in range(3):
            new_audience = set(
                map(str, self.objects(subject=subject, predicate=HAS_TRANSIENT_AUDIENCE))
            )
            if audience == new_audience:
                break
            for recipient in new_audience:
                if recipient != PUBLIC_ACTOR and recipient not in audience:
                    self.pull(recipient, actor)
            audience = new_audience

        inboxes = self.objects(subject=subject, predicate=HAS_TRANSIENT_INBOXES)
        inbox_set = set(map(str, inboxes))
        self._logger.debug("Resolved %s to %d inboxes", subject, len(inbox_set))

        return inbox_set

    def push(self, subject: str) -> tuple[set[Response], set[Response]]:
        self._logger.info("Pushing %s to its audience", subject)

        actor = self.value(subject=subject, predicate=HAS_ACTOR)
        if not actor:
            raise TypeError(f"{subject} has no actor; can only push activities")
        self._logger.debug("Actor for %s is %s", subject, actor)

        targets = self.get_all_targets(subject, actor)

        succeeded = set()
        failed = set()
        for target in targets:
            success, res = self.push_to(target, subject, actor)
            if success:
                succeeded.add(res)
            else:
                failed.add(res)

        return succeeded, failed
