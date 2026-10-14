class EventNotFoundException(Exception):
    def __init__(self, event_id: str):
        self.event_id = event_id
        super().__init__(f"Event '{event_id}' not found.")


class DuplicateEventException(Exception):
    def __init__(self, event_id: str):
        self.event_id = event_id
        super().__init__(f"Event '{event_id}' already exists.")


class CategoryNotFoundException(Exception):
    def __init__(self, category_id: int):
        self.category_id = category_id
        super().__init__(f"Category with id '{category_id}' not found.")


class ArchiveException(Exception):
    pass


class CacheException(Exception):
    pass
