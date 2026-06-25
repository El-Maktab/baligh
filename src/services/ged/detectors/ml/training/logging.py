"""Small logging helpers for long-running GED ML training jobs."""


def log(message: str) -> None:
    """Print a flush-always training log line."""
    print(message, flush=True)


def format_seconds(seconds: float) -> str:
    """Format elapsed seconds for human-readable logs."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remaining = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {remaining:.1f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {remaining:.1f}s"
