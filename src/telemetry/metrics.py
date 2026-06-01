from __future__ import annotations


def normalize_error_code(error: BaseException) -> str:
    if isinstance(error, FileNotFoundError):
        return "DATASET_NOT_FOUND"
    if isinstance(error, ValueError):
        return "VALUE_ERROR"
    if isinstance(error, RuntimeError):
        return "PROVIDER_ERROR"
    return "INTERNAL_ERROR"
