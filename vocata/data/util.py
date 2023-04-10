def jsonld_single(doc: dict, id_: str, key_: str = "id") -> dict:
    if "@graph" not in doc:
        if doc.get(key_) == id_:
            return doc
        raise KeyError(f"Input is a single object, but is not {id_}")

    new_doc = {}

    if "@context" in doc:
        new_doc["@context"] = doc["@context"]

    found = False
    for obj in doc["@graph"]:
        if obj[key_] == id_:
            new_doc.update(obj)
            found = True
            break

    if not found:
        raise KeyError(f"{id_} not found in graph")

    return new_doc
