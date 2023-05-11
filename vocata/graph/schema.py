# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from rdflib.namespace import Namespace, RDF

AS_URI = "https://www.w3.org/ns/activitystreams#"
AS = Namespace(AS_URI)

VOC_URI = "https://docs.vocata.one/information-schema#"
VOC = Namespace(VOC_URI)

LDP_URI = "http://www.w3.org/ns/ldp#"
LDP = Namespace(LDP_URI)

SEC_URI = "https://w3id.org/security#"
SEC = Namespace(SEC_URI)

# FIXME support intransitive activities
# FIXME disover from a real schema
ACTIVITY_TYPES = {
    AS.Accept,
    AS.Add,
    AS.Announce,
    AS.Arrive,
    AS.Block,
    AS.Create,
    AS.Delete,
    AS.Dislike,
    AS.Flag,
    AS.Follow,
    AS.Ignore,
    AS.Invite,
    AS.Join,
    AS.Leave,
    AS.Like,
    AS.Listen,
    AS.Move,
    AS.Offer,
    AS.Question,
    AS.Reject,
    AS.Read,
    AS.Remove,
    AS.TentativeReject,
    AS.TentativeAccept,
    AS.Travel,
    AS.Undo,
    AS.Update,
    AS.View,
}
ACTIVITY_TOUCHES = AS.actor | AS.instrument | AS.object | AS.origin | AS.target
ACTOR_TYPES = {AS.Application, AS.Group, AS.Organization, AS.Person, AS.Service}
OBJECT_TYPES = {
    AS.Article,
    AS.Audio,
    AS.Document,
    AS.Event,
    AS.Image,
    AS.Note,
    AS.Page,
    AS.Place,
    AS.Profile,
    AS.Relationship,
    AS.Tombstone,
    AS.Video,
}
LINK_TYPES = {
    AS.Mention,
}


__all__ = ["AS", "VOC", "LDP", "RDF", "SEC"]
