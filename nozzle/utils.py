
def blockid_to_blocknumber(block_id):
    return int(block_id[:8], base=16)
