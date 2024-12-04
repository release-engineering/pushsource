def open_src_local(item):
    # default opener for the push items
    # assumes that the item's 'src' points to the
    # locally-accessible file
    return open(item.src, "rb")
