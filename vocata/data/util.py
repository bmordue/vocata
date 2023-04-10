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


def jsonld_cleanup_ids(doc: dict, key_: str = "id", flatten: bool = True) -> None:
    new_doc = {}
    for attr, value in doc.items():
        if isinstance(value, list):
            new_list = []
            for elem in value:
                if isinstance(elem, dict):
                    new_elem = jsonld_cleanup_ids(elem, key_)
                    if new_elem:
                        new_list.append(new_elem)
                else:
                    new_list.append(elem)
        elif isinstance(value, dict):
            new_value = jsonld_cleanup_ids(value, key_)
            if new_value:
                new_doc[attr] = new_value
        elif attr != key_ or not value.startswith("_:"):
            new_doc[attr] = value

    if flatten and len(new_doc) == 1 and key_ in new_doc:
        return new_doc[key_]

    return new_doc
