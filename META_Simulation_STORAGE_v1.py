
# creates the empty storage = beginning state
def create_empty_storage():
    return {}

# function to add one line of the Infeed-Excel to the storage; distinguishes article_code and cratey_type
def add_crates_to_storage(storage, infeed):
    key = (infeed.article_code, infeed.crate_type)
    storage[key] = storage.get(key, 0) + infeed.quantity

