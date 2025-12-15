"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from wt_registry.models import RegistryEntry, RegistryMetadata


def test_registry_metadata_minimal() -> None:
    """Test creating RegistryMetadata with minimal required fields."""
    metadata = RegistryMetadata(
        title="Test Function", description="A test function for unit testing"
    )

    assert metadata.title == "Test Function"
    assert metadata.description == "A test function for unit testing"
    assert metadata.tags == []
    assert metadata.deprecated is False
    assert metadata.deprecation_message is None


def test_registry_metadata_with_tags() -> None:
    """Test creating RegistryMetadata with tags."""
    metadata = RegistryMetadata(
        title="Database Query",
        description="Execute a database query",
        tags=["database", "io", "query"],
    )

    assert metadata.tags == ["database", "io", "query"]


def test_registry_metadata_with_deprecation() -> None:
    """Test creating RegistryMetadata with deprecation info."""
    metadata = RegistryMetadata(
        title="Old Function",
        description="Legacy function",
        deprecated=True,
        deprecation_message="Use new_function instead for better performance",
    )

    assert metadata.deprecated is True
    assert metadata.deprecation_message == "Use new_function instead for better performance"


def test_registry_metadata_all_fields() -> None:
    """Test creating RegistryMetadata with all fields populated."""
    metadata = RegistryMetadata(
        title="Complete Example",
        description="Example with all fields",
        tags=["example", "test"],
        deprecated=True,
        deprecation_message="Deprecated",
    )

    assert metadata.title == "Complete Example"
    assert metadata.description == "Example with all fields"
    assert metadata.tags == ["example", "test"]
    assert metadata.deprecated is True
    assert metadata.deprecation_message == "Deprecated"


def test_registry_metadata_validation_missing_title() -> None:
    """Test that RegistryMetadata requires title field."""
    with pytest.raises(PydanticValidationError) as exc_info:
        RegistryMetadata(description="Missing title")  # type: ignore

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("title",) for error in errors)


def test_registry_metadata_validation_missing_description() -> None:
    """Test that RegistryMetadata requires description field."""
    with pytest.raises(PydanticValidationError) as exc_info:
        RegistryMetadata(title="Missing description")  # type: ignore

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("description",) for error in errors)


def test_registry_metadata_serialization() -> None:
    """Test that RegistryMetadata can be serialized to dict."""
    metadata = RegistryMetadata(
        title="Serialize Test",
        description="Test serialization",
        tags=["test"],
        deprecated=True,
        deprecation_message="Use v2",
    )

    data = metadata.model_dump()
    assert data["title"] == "Serialize Test"
    assert data["description"] == "Test serialization"
    assert data["tags"] == ["test"]
    assert data["deprecated"] is True
    assert data["deprecation_message"] == "Use v2"


def test_registry_entry_minimal() -> None:
    """Test creating RegistryEntry with minimal fields."""
    metadata = RegistryMetadata(title="Test", description="Test function")
    entry = RegistryEntry(
        metadata=metadata,
        module_path="myapp.tasks",
        function_name="test_func",
        json_schema={"type": "object", "properties": {}},
    )

    assert entry.metadata == metadata
    assert entry.module_path == "myapp.tasks"
    assert entry.function_name == "test_func"
    assert entry.json_schema == {"type": "object", "properties": {}}


def test_registry_entry_fully_qualified_name() -> None:
    """Test the fully_qualified_name computed property."""
    metadata = RegistryMetadata(title="Test", description="Test")
    entry = RegistryEntry(
        metadata=metadata,
        module_path="mypackage.submodule.tasks",
        function_name="process_data",
        json_schema={},
    )

    assert entry.fully_qualified_name == "mypackage.submodule.tasks.process_data"


def test_registry_entry_import_statement() -> None:
    """Test the import_statement computed property."""
    metadata = RegistryMetadata(title="Test", description="Test")
    entry = RegistryEntry(
        metadata=metadata,
        module_path="mypackage.utils",
        function_name="helper_function",
        json_schema={},
    )

    assert entry.import_statement == "from mypackage.utils import helper_function"


def test_registry_entry_with_complex_schema() -> None:
    """Test RegistryEntry with a complex JSON schema."""
    metadata = RegistryMetadata(
        title="Complex Function", description="Function with complex schema"
    )
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "age"],
    }
    entry = RegistryEntry(
        metadata=metadata, module_path="app.users", function_name="create_user", json_schema=schema
    )

    assert entry.json_schema == schema
    assert "properties" in entry.json_schema
    assert "name" in entry.json_schema["properties"]


def test_registry_entry_serialization() -> None:
    """Test that RegistryEntry can be serialized to dict."""
    metadata = RegistryMetadata(
        title="Serialize Entry", description="Test entry serialization", tags=["test"]
    )
    entry = RegistryEntry(
        metadata=metadata,
        module_path="test.module",
        function_name="serialize_test",
        json_schema={"type": "function"},
    )

    data = entry.model_dump()
    assert data["metadata"]["title"] == "Serialize Entry"
    assert data["module_path"] == "test.module"
    assert data["function_name"] == "serialize_test"
    assert data["json_schema"] == {"type": "function"}


def test_registry_entry_json_mode_serialization() -> None:
    """Test that RegistryEntry can be serialized in JSON mode."""
    metadata = RegistryMetadata(title="JSON Test", description="Test JSON serialization")
    entry = RegistryEntry(
        metadata=metadata,
        module_path="test.json",
        function_name="json_test",
        json_schema={"type": "object"},
    )

    data = entry.model_dump(mode="json")
    assert isinstance(data, dict)
    assert data["metadata"]["title"] == "JSON Test"
    assert data["module_path"] == "test.json"


def test_registry_entry_validation_missing_metadata() -> None:
    """Test that RegistryEntry requires metadata field."""
    with pytest.raises(PydanticValidationError) as exc_info:
        RegistryEntry(  # type: ignore
            module_path="test", function_name="func", json_schema={}
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("metadata",) for error in errors)


def test_registry_entry_validation_missing_module_path() -> None:
    """Test that RegistryEntry requires module_path field."""
    metadata = RegistryMetadata(title="Test", description="Test")
    with pytest.raises(PydanticValidationError) as exc_info:
        RegistryEntry(metadata=metadata, function_name="func", json_schema={})  # type: ignore

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("module_path",) for error in errors)


def test_registry_entry_validation_missing_function_name() -> None:
    """Test that RegistryEntry requires function_name field."""
    metadata = RegistryMetadata(title="Test", description="Test")
    with pytest.raises(PydanticValidationError) as exc_info:
        RegistryEntry(metadata=metadata, module_path="test", json_schema={})  # type: ignore

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("function_name",) for error in errors)


def test_registry_entry_validation_missing_json_schema() -> None:
    """Test that RegistryEntry requires json_schema field."""
    metadata = RegistryMetadata(title="Test", description="Test")
    with pytest.raises(PydanticValidationError) as exc_info:
        RegistryEntry(  # type: ignore
            metadata=metadata, module_path="test", function_name="func"
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("json_schema",) for error in errors)
