import pyarrow as pa
from google.protobuf.descriptor import FieldDescriptor
from pyarrow.lib import Field


def protobuf_type_to_pyarrow(field_descriptor: FieldDescriptor) -> pa.DataType:
    """Map Protobuf field types to PyArrow types."""

    # Handle repeated fields (which are not optional)
    if field_descriptor.label == FieldDescriptor.LABEL_REPEATED:
        arrow_type = protobuf_type_to_pyarrow_single(field_descriptor)
        return pa.list_(arrow_type)

    # Handle optional fields by making them nullable
    return protobuf_type_to_pyarrow_single(field_descriptor)


def protobuf_type_to_pyarrow_single(field_descriptor: FieldDescriptor) -> pa.DataType:
    """Map single Protobuf field types to PyArrow types."""
    if field_descriptor.type == FieldDescriptor.TYPE_STRING:
        return pa.string()
    elif field_descriptor.type == FieldDescriptor.TYPE_INT32:
        return pa.int32()
    elif field_descriptor.type == FieldDescriptor.TYPE_INT64:
        return pa.int64()
    elif field_descriptor.type == FieldDescriptor.TYPE_UINT64:
        return pa.uint64()
    elif field_descriptor.type == FieldDescriptor.TYPE_UINT32:
        return pa.uint32()
    elif field_descriptor.type == FieldDescriptor.TYPE_BOOL:
        return pa.bool_()
    elif field_descriptor.type == FieldDescriptor.TYPE_FLOAT:
        return pa.float32()
    elif field_descriptor.type == FieldDescriptor.TYPE_DOUBLE:
        return pa.float64()
    elif field_descriptor.type == FieldDescriptor.TYPE_BYTES:
        return pa.binary()
    elif field_descriptor.type == FieldDescriptor.TYPE_ENUM:
        # Map enums to their string representation
        return pa.dictionary(pa.int32(), pa.string())
    elif field_descriptor.type == FieldDescriptor.TYPE_MESSAGE:
        # Nested message: Create a Struct type
        nested_class = field_descriptor.message_type
        return pa.struct(generate_pyarrow_fields_from_descriptor(nested_class))
    else:
        raise TypeError(f"Unsupported Protobuf field type: {field_descriptor.type}")


def generate_pyarrow_fields_from_descriptor(descriptor: FieldDescriptor) -> list[Field]:
    """Generate PyArrow fields from a Protobuf Descriptor."""
    fields = []

    for field in descriptor.fields:
        arrow_type = protobuf_type_to_pyarrow(field)
        fields.append(pa.field(field.name, arrow_type, nullable=True))  # Set everything to nullable

    return fields


def generate_pyarrow_schema_from_protobuf(proto_class) -> pa.Schema:
    """Generate a PyArrow schema from a Protobuf message class."""
    descriptor = proto_class.DESCRIPTOR
    fields = generate_pyarrow_fields_from_descriptor(descriptor)
    return pa.schema(fields)
