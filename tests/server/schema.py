# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Any, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, Field, validator

AS_URI = "https://www.w3.org/ns/activitystreams"
SEC_URI = "https://w3id.org/security/v1"


class Object(BaseModel):
    context_: AnyHttpUrl | list[AnyHttpUrl | dict[str, str]] | dict[
        str, AnyHttpUrl | dict[str, str]
    ] = Field(alias="@context")
    id: Optional[AnyHttpUrl] = None
    # FIXME can very much have multiple types
    type: str

    # FIXME create subtypes with more specific properties
    # FIXME use correct types
    attachment: Any
    attributedTo: Any
    audience: Any
    content: Any
    context: Any
    contentMap: Any
    name: Any
    nameMap: Any
    endtTime: Any
    generator: Any
    icon: Any
    image: Any
    inReplyTo: Any
    location: Any
    preview: Any
    published: Any
    replies: Any
    startTime: Any
    summary: Any
    summaryMap: Any
    tag: Any
    updated: Any
    url: Any
    to: Any
    bto: Any
    cc: Any
    bcc: Any
    mediaType: Any
    duration: Any

    shares: Any
    likes: Any
    source: Any

    alsoKnownAs: Any

    @validator("context_")
    def context_must_include_as(cls, v):
        if isinstance(v, str) and v == AS_URI or isinstance(v, list) and AS_URI in v:
            return v
        raise ValueError(f"@context must include {AS_URI}")


class Link(BaseModel):
    id: Optional[AnyHttpUrl] = None
    type: Literal["Link"]

    href: Any
    hrefLang: Any
    name: Any
    mediaType: Any
    rel: Any
    height: Any
    wifth: Any


class Actor(Object):
    # FIXME make proper subtypes
    type: Literal["Application", "Group", "Organization", "Person", "Service"]

    inbox: AnyHttpUrl
    outbox: Optional[AnyHttpUrl]

    endpoints: Any
    following: Any
    followers: Any
    liked: Any
    preferredUsername: Any
    streams: Any

    @validator("context_")
    def context_must_include_sec(cls, v):
        if isinstance(v, list) and SEC_URI in v:
            return v
        raise ValueError(f"@context must include {SEC_URI}")


class Activity(Object):
    # FIXME make proper subtypes
    type: str

    actor: Any
    object: Any
    target: Any
    origin: Any
    result: Any
    instrument: Any


class IntransitiveActivity(Activity):
    # FIXME make proper subtypes
    type: str

    object: None = None


class Collection(Object):
    type: Literal["Collection"]

    totalItems: Optional[int] = None
    items: Optional[list[str | dict[str, str]]] = None

    first: Any
    last: Any
    current: Any


class CollectionPage(Collection):
    type: Literal["CollectionPage"]

    partOf: Any
    prev: Any
    next: Any


class OrderedCollection(Collection):
    type: Literal["OrderedCollection"]

    items: None = None
    orderedItems: Optional[list[str | dict[str, str]]] = None


class OrderedCollectionPage(CollectionPage):
    type: Literal["OrderedCollectionPage"]

    items: None = None
    orderedItems: Optional[list[str | dict[str, str]]] = None

    partOf: Any
    prev: Any
    next: Any
    startIndex: Any
