"""Command-line interface for wt-registry."""

import argparse
import json
import sys
from types import MappingProxyType
from typing import Any

from wt_registry.models import RegistryEntry
from wt_registry.registry import get_registry


def filter_by_function_names(
    registry: MappingProxyType[str, RegistryEntry],
    function_names: list[str] | None = None,
) -> dict[str, RegistryEntry]:
    """
    Filter registry entries by function names.

    Args:
        registry: Full registry from get_registry()
        function_names: List of function names to include (None = include all)

    Returns:
        Filtered dictionary of FQN -> RegistryEntry

    Examples:
        >>> from wt_registry.models import RegistryMetadata, RegistryEntry
        >>> from wt_registry.registry import register_entry, clear_registry
        >>> from types import MappingProxyType
        >>> clear_registry()
        >>> def test_func(x: int) -> str:
        ...     return str(x)
        >>> metadata = RegistryMetadata(title="Test", description="Test")
        >>> entry = RegistryEntry(
        ...     metadata=metadata,
        ...     module_path="test",
        ...     function_name="test_func",
        ... )
        >>> entry._func_ref = test_func
        >>> register_entry(entry)
        >>> from wt_registry.registry import get_registry
        >>> registry = get_registry()
        >>> filtered = filter_by_function_names(registry, ["test_func"])
        >>> len(filtered)
        1
        >>> "test.test_func" in filtered
        True
    """
    if function_names is None:
        return dict(registry)

    filtered = {}
    for fqn, entry in registry.items():
        if entry.function_name in function_names:
            filtered[fqn] = entry
    return filtered


def serialize_entries(
    entries: dict[str, RegistryEntry],
) -> dict[str, dict[str, Any]]:
    """
    Serialize registry entries to JSON-compatible dict.

    Only generates JSON schema for entries being serialized (performance optimization).

    Args:
        entries: Filtered registry entries

    Returns:
        Serialized registry data

    Examples:
        >>> from wt_registry.models import RegistryMetadata, RegistryEntry
        >>> from wt_registry.registry import clear_registry
        >>> clear_registry()
        >>> def sample_func(x: int) -> str:
        ...     return str(x)
        >>> metadata = RegistryMetadata(title="Sample", description="Sample function")
        >>> entry = RegistryEntry(
        ...     metadata=metadata,
        ...     module_path="test",
        ...     function_name="sample_func",
        ... )
        >>> entry._func_ref = sample_func
        >>> entries = {"test.sample_func": entry}
        >>> data = serialize_entries(entries)
        >>> "test.sample_func" in data
        True
        >>> data["test.sample_func"]["metadata"]["title"]
        'Sample'
        >>> "json_schema" in data["test.sample_func"]
        True
    """
    registry_data = {}
    for fqn, entry in entries.items():
        data = entry.model_dump(mode="json")
        # Manually add json_schema since it's a property, not a field
        # This triggers lazy generation only for selected functions
        data["json_schema"] = entry.json_schema
        registry_data[fqn] = data
    return registry_data


def format_pretty(entries: dict[str, RegistryEntry]) -> str:
    """
    Format registry entries as human-readable text.

    Args:
        entries: Filtered registry entries

    Returns:
        Multi-line formatted string

    Examples:
        >>> from wt_registry.models import RegistryMetadata, RegistryEntry
        >>> def pretty_func(x: int) -> str:
        ...     return str(x)
        >>> metadata = RegistryMetadata(
        ...     title="Pretty Function",
        ...     description="A function for pretty printing",
        ...     tags=["test", "pretty"]
        ... )
        >>> entry = RegistryEntry(
        ...     metadata=metadata,
        ...     module_path="test.module",
        ...     function_name="pretty_func",
        ... )
        >>> entry._func_ref = pretty_func
        >>> entries = {"test.module.pretty_func": entry}
        >>> output = format_pretty(entries)
        >>> "=== test.module.pretty_func ===" in output
        True
        >>> "Title: Pretty Function" in output
        True
        >>> "Tags: test, pretty" in output
        True
    """
    if not entries:
        return "No functions registered"

    lines = []
    for fqn, entry in entries.items():
        lines.append(f"=== {fqn} ===")
        lines.append(f"Title: {entry.metadata.title}")
        lines.append(f"Description: {entry.metadata.description}")

        if entry.metadata.tags:
            lines.append(f"Tags: {', '.join(entry.metadata.tags)}")

        if entry.metadata.deprecated:
            if entry.metadata.deprecation_message:
                lines.append(f"Deprecated: Yes ({entry.metadata.deprecation_message})")
            else:
                lines.append("Deprecated: Yes")
        else:
            lines.append("Deprecated: No")

        lines.append(f"Import: {entry.import_statement}")
        lines.append("")  # Empty line between entries

    return "\n".join(lines)


def main() -> None:
    """
    Main CLI entry point.

    Parses command-line arguments and exports the registry to stdout
    in either JSON or pretty format, with optional filtering by function names.
    """
    parser = argparse.ArgumentParser(
        description="Export wt-registry to JSON or human-readable format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--format",
        choices=["json", "pretty"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--function",
        action="append",
        dest="function_names",
        metavar="NAME",
        help="Filter by function name (can be specified multiple times)",
    )

    args = parser.parse_args()

    try:
        # Get registry
        registry = get_registry()

        # Apply filters
        filtered_entries = filter_by_function_names(registry, args.function_names)

        # Format and output
        if args.format == "json":
            serialized = serialize_entries(filtered_entries)
            output = json.dumps(serialized, indent=2)
            print(output)
        else:  # pretty
            output = format_pretty(filtered_entries)
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
