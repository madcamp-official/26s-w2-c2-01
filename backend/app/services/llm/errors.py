class LLMQuotaExceededError(RuntimeError):
    """Raised when the configured LLM provider rejects a request for quota reasons."""

    def __init__(self) -> None:
        super().__init__(
            "AI 사용량 한도를 초과했습니다. 잠시 후 또는 할당량이 초기화된 뒤 다시 시도해 주세요."
        )
