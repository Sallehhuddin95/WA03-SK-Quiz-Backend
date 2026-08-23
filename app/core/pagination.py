from app.core.exceptions import InvalidPaginationError

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


def normalize_pagination(
    page: int | None,
    page_size: int | None,
    default_page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[int, int]:
    page = 1 if page is None else page
    page_size = default_page_size if page_size is None else page_size
    if page < 1 or page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise InvalidPaginationError()
    return page, page_size


def build_meta(
    page: int, page_size: int, total_items: int
) -> dict[str, int]:
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
    }