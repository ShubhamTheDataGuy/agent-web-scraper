from typing import TypedDict

class InputState(TypedDict):
    url: str

class OutputState(TypedDict):
    result: str

class GraphState(TypedDict):
    url: str
    url_batches: list
    scraped_data: list
    formatted_data: list
    error: str
    retry_count: int
    failed_node: str