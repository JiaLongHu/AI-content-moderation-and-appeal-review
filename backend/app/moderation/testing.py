from collections import deque

from backend.app.moderation.schemas import ModerationOutput


class StubAIReviewer:
    def __init__(self, *results: ModerationOutput | Exception) -> None:
        self.results = deque(results)
        self.calls: list[tuple[str, str | None]] = []

    async def review(self, text: str, context: str | None = None) -> ModerationOutput:
        self.calls.append((text, context))
        if not self.results:
            raise RuntimeError("StubAIReviewer has no queued result")
        result = self.results.popleft()
        if isinstance(result, Exception):
            raise result
        return result
