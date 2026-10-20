STAGE_FETCH = "fetch"
STAGE_LLM = "llm"
STAGE_ALL_NULL = "all_null"
STAGE_CRASH = "crash"


class MosqueScrapeError(Exception):
    """One mosque could not be updated. The cause is reported to Sentry where it happened."""

    def __init__(self, mosque: str, stage: str):
        super().__init__(f"{mosque} ({stage})")
        self.mosque = mosque
        self.stage = stage


class ScrapeJobFailed(Exception):
    """Raised after a run that left at least one mosque un-updated, so the cron check-in fails."""

    def __init__(self, failures: list[MosqueScrapeError], total: int):
        failed = ", ".join(str(f) for f in failures)
        super().__init__(f"{len(failures)}/{total} mosques failed: {failed}")
        self.failures = failures
