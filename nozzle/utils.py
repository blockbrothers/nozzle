
def blockid_to_blocknumber(block_id):
    return int(block_id[:8], base=16)


def get_first_or_none(data):
    try:
        return data[0]
    except (TypeError, IndexError):
        return None
