"""Formatter for search results to create token-efficient, human-readable output."""

from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from igloo_mcp.converter import TruncationMetadata


def format_search_results(
    results: list[dict[str, Any]],
    search_params: dict[str, Any],
    total_found: int,
) -> str:
    """
    Format search results into a concise, human-readable string optimized for LLM token efficiency.

    Args:
        results: List of search result dictionaries with fields like title, type, url, etc.
        search_params: Dictionary containing the search parameters used (query, applications, etc.)
        total_found: Total number of results found by the search

    Returns:
        A formatted string containing the search results with header and individual result sections.
    """
    header = _format_header(search_params, total_found)
    
    if not results:
        return f"{header}\n\nNo results found."
    
    formatted_results = [header]
    
    for result in results:
        formatted_results.append("\n----------\n")
        formatted_results.append(_format_single_result(result))
    
    formatted_results.append("\n----------")
    
    return "".join(formatted_results)


def _format_header(search_params: dict[str, Any], total_found: int) -> str:
    """Format search results header with query parameters."""
    query = search_params.get("query")
    query_str = f'"{query}"' if query else "All"
    
    applications = search_params.get("applications")
    if applications:
        apps_str = ", ".join(applications)
    else:
        apps_str = "All"
    
    sort = search_params.get("sort", "default")
    
    limit = search_params.get("limit")
    limit_str = str(limit) if limit is not None else "None"
    
    header_parts = [
        f"Applications: {apps_str}",
        f"Sort: {sort}",
        f"Limit: {limit_str}",
        f"Total Results Found: {total_found}",
    ]
    
    parent_href = search_params.get("parent_href")
    if parent_href:
        header_parts.insert(1, f"Parent: {parent_href}")
    
    updated_date_type = search_params.get("updated_date_type")
    if updated_date_type:
        date_filter = _format_date_filter(updated_date_type, search_params)
        header_parts.insert(1, date_filter)
    
    header = f"Search Results for Query: {query_str} ({' | '.join(header_parts)}):"
    
    return header


def _format_date_filter(updated_date_type: str, search_params: dict[str, Any]) -> str:
    """Format the date filter information for the header."""
    if updated_date_type == "custom_range":
        date_from = search_params.get("updated_date_range_from")
        date_to = search_params.get("updated_date_range_to")
        if date_from and date_to:
            return f"Date Filter: {date_from} to {date_to}"
        return "Date Filter: Custom Range"
    
    date_type_display = updated_date_type.replace("_", " ").title()
    return f"Date Filter: {date_type_display}"


def _format_single_result(result: dict[str, Any]) -> str:
    """Format a single search result."""
    lines = []
    
    lines.append(f"Title: {result.get('title', 'Untitled')}")
    lines.append(f"Type: {result.get('type', 'unknown')}")
    lines.append(f"URL: {result.get('full_url', '')}")
    
    modified_date = result.get("modified_date")
    if modified_date:
        formatted_date = _format_date(modified_date)
        lines.append(f"Last Modified: {formatted_date}")
    
    description = (result.get("description") or "").strip()
    content = (result.get("content") or "").strip()
    
    text_to_show = description or content
    if text_to_show:
        truncated_text = _truncate_text(text_to_show, max_length=200)
        field_name = "Description" if description else "Content"
        lines.append(f"{field_name}: {truncated_text}")
    
    views = result.get("views_count", 0)
    comments = result.get("comments_count", 0)
    likes = result.get("likes_count", 0)
    lines.append(f"Views: {views} | Comments: {comments} | Likes: {likes}")
    
    labels = result.get("labels", {})
    if labels:
        label_names = [str(name) for name in labels.values()]
        if label_names:
            lines.append(f"Labels: {', '.join(label_names)}")
    
    if result.get("is_recommended"):
        lines.append("* This item is recommended")
    
    if result.get("is_archived"):
        lines.append("* This item is archived")
    
    return "\n".join(lines)


def _format_date(date_str: str) -> str:
    """
    Parse an ISO format date string and return it in YYYY-MM-DD format.
    
    Args:
        date_str: ISO format date string (e.g., "2025-11-06T14:20:28.85-05:00")
    
    Returns:
        Date in YYYY-MM-DD format, or the original string if parsing fails
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime(r"%Y-%m-%d")
    except (ValueError, AttributeError):
        if isinstance(date_str, str) and len(date_str) >= 10 and date_str[4] == "-" and date_str[7] == "-":
            return date_str[:10]
        return str(date_str)


def _truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to a maximum length, adding ellipsis if truncated.
    
    Args:
        text: The text to truncate
        max_length: Maximum length (default 200)
    
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length].rsplit(" ", 1)[0]
    return f"{truncated}..."


def format_fetch_result(
    url: str,
    markdown: str,
    start_index: int | None = None,
) -> str:
    """
    Format the fetch result for LLM consumption.

    Args:
        url: The URL that was fetched.
        markdown: The converted Markdown content.
        start_index: Character offset if reading from a continuation point.
            When provided, adds position context to the header.

    Returns:
        Formatted string with URL header and Markdown content.
    """
    header_parts = ["# Fetched Content", "", f"URL: {url}"]
    
    if start_index is not None and start_index > 0:
        header_parts.append(f"Reading from offset: {start_index:,}")
    
    header_parts.extend(["", "---", "", ""])
    header = "\n".join(header_parts)
    return header + markdown


def format_fetch_results(results: list[dict[str, str]], total_count: int) -> str:
    """
    Format multiple fetch results for LLM consumption.

    Each page is formatted with a clear header showing its position and URL,
    with separators between pages for easy reading.

    Args:
        results: List of dictionaries with 'url', 'markdown' (content), and optionally 'error'.
        total_count: Total number of pages being fetched (for display in headers).

    Returns:
        Formatted string with all pages concatenated with clear separators.
    """
    if not results:
        return "No pages to display."

    formatted_parts = []
    
    for i, result in enumerate(results, start=1):
        url = result.get("url", "Unknown URL")
        markdown = result.get("markdown", "")
        error = result.get("error")
        
        header = f"===== PAGE {i} of {total_count} =====\nURL: {url}\n"
        
        if error:
            content = f"\n[Error fetching page: {error}]\n"
        else:
            content = f"\n{markdown}\n"
        
        formatted_parts.append(header + content)
    
    return "\n".join(formatted_parts)


def format_truncation_metadata(metadata: "TruncationMetadata", url: str) -> str:
    """
    Format truncation metadata with clear instructions for continuation.
    
    Output format optimized for LLM comprehension with:
    - Visual warning indicator for truncation
    - Percentage showing document completeness
    - Clear action instructions for continuation
    """
    # Calculate percentage with divide-by-zero protection
    pct = int(100 * metadata.chars_returned / metadata.chars_total) if metadata.chars_total > 0 else 0
    
    lines = [
        "",
        "---",
        "",
        "⚠️ CONTENT TRUNCATED",
        f"Showing {metadata.chars_returned:,} of {metadata.chars_total:,} chars ({pct}% of document)",
    ]
    
    if metadata.current_path:
        lines.append(f"Current section: {metadata.current_path}")
    
    if metadata.remaining_sections:
        sections_str = ", ".join(metadata.remaining_sections)
        lines.append(f"Upcoming sections: {sections_str}")
    
    if metadata.next_start_index is not None:
        lines.extend([
            "",
            "To continue reading, call fetch with start_index:",
            f'  fetch(url="{url}", start_index={metadata.next_start_index})',
        ])
    
    return "\n".join(lines)


def format_member_search_results(
    results: list[dict[str, Any]],
    query: str,
    community_url: str = "",
) -> str:
    """
    Format member search results for LLM consumption.
    Returns basic info only (no profile details). Use format_member_profile for details.
    
    Args:
        results: List of raw member records from the API
        query: The original search query
        community_url: The base URL of the Igloo community (for building profile URLs)
    
    Returns:
        A formatted string containing the member search results with basic info.
    """
    header = f'Members found for query: "{query}" (Total Results Found: {len(results)}):'
    
    if not results:
        return f"{header}\n\nNo results found."
    
    formatted_results = [header]
    
    for member in results:
        formatted_results.append("\n----------\n")
        formatted_results.append(_format_member_basic_info(member, community_url))
    
    formatted_results.append("\n----------")
    
    return "".join(formatted_results)


def _format_member_basic_info(member: dict[str, Any], community_url: str = "") -> str:
    """
    Format basic info for a single member (used in search results).
    Minimal output to save tokens - use fetch_member for full details.
    
    Args:
        member: Raw member record from the API
        community_url: Base URL for building profile links (unused, kept for API compatibility)
    """
    name_info = member.get("name", {})
    full_name = name_info.get("fullName", "Unknown")
    email = member.get("email", "N/A")
    member_id = member.get("id", "N/A")
    
    lines = [
        f"Name: {full_name}",
        f"Email: {email}",
        f"Member ID: {member_id}",
    ]
    
    return "\n".join(lines)


# Map raw API profile field names to display labels (whitelist approach)
# Only fields in this mapping will be included in the output
PROFILE_FIELD_MAPPING = {
    "title": "Job Title",
    "department": "Department",
    "i_report_to_email": "Manager Email",
    "office_location": "Office",
    "desk_number": "Desk",
    "busphone": "Work Phone",
    "extension": "Extension",
    "cellphone": "Mobile",
    "work_start_date": "Start Date",
}


def format_member_profile(
    member_info: dict[str, Any],
    profile_items: list[dict[str, Any]],
    manager_name: str | None,
    community_url: str = "",
) -> str:
    """
    Format detailed member profile for LLM consumption.
    
    Args:
        member_info: Raw member info from get_member_info API call
        profile_items: List of raw profile items from get_member_profile API call
        manager_name: Manager's full name (fetched separately), or None
        community_url: The base URL of the Igloo community
    
    Returns:
        A formatted string containing the detailed member profile.
    """
    name_info = member_info.get("name", {})
    full_name = name_info.get("fullName", "Unknown")
    email = member_info.get("email", "N/A")
    username = member_info.get("namespace", "N/A")
    profile_url = f"{community_url}/.profile/{username}" if community_url and username else "N/A"
    
    lines = [
        f"Member Profile: {full_name}",
        "----------",
        f"Name: {full_name}",
        f"Email: {email}",
        f"Username: {username}",
        f"Profile URL: {profile_url}",
    ]
    
    # Add manager name if available
    if manager_name:
        lines.append(f"Manager Name: {manager_name}")
    
    # Process raw profile items using whitelist
    for item in profile_items:
        field_name = item.get("Name", "")
        field_value = item.get("Value", "")
        
        # Skip empty or null values
        if not field_value or field_value in ("null", "https://bluejeans.com/null"):
            continue
        
        # Get display label from whitelist
        label = PROFILE_FIELD_MAPPING.get(field_name)
        if not label:
            continue  # Only show fields in the whitelist
        
        # Clean up date format
        if "date" in field_name and " " in str(field_value):
            field_value = str(field_value).split(" ")[0]
        
        lines.append(f"{label}: {field_value}")
    
    lines.append("----------")
    
    return "\n".join(lines)
