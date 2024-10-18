from functools import cache
from typing import List, Any

import pyarrow as pa
from google.protobuf.descriptor import FieldDescriptor


def protobuf_to_pyarrow_schema(message_descriptor):
    fields = []

    for field in message_descriptor.fields:
        if field.type == FieldDescriptor.TYPE_MESSAGE:
            if field.label == FieldDescriptor.LABEL_REPEATED:
                # Repeated struct: create list fields for each nested variable
                nested_fields = protobuf_to_pyarrow_schema(field.message_type)
                for nested_field in nested_fields:
                    fields.append(
                        pa.field(
                            f"{field.name}.{nested_field.name}",
                            pa.list_(nested_field.type),
                        )
                    )
            else:
                # Non-repeated struct: flatten nested variables
                nested_fields = protobuf_to_pyarrow_schema(field.message_type)
                fields.extend(
                    [
                        pa.field(f"{field.name}.{nested_field.name}", nested_field.type)
                        for nested_field in nested_fields
                    ]
                )
        else:
            # Non-struct field
            pa_type = protobuf_type_to_pyarrow_type(field)
            if field.label == FieldDescriptor.LABEL_REPEATED:
                pa_type = pa.list_(pa_type)
            fields.append(pa.field(field.name, pa_type))

    return fields


def protobuf_type_to_pyarrow_type(field):
    type_mapping = {
        FieldDescriptor.TYPE_DOUBLE: pa.float64(),
        FieldDescriptor.TYPE_FLOAT: pa.float32(),
        FieldDescriptor.TYPE_INT64: pa.int64(),
        FieldDescriptor.TYPE_UINT64: pa.uint64(),
        FieldDescriptor.TYPE_INT32: pa.int32(),
        FieldDescriptor.TYPE_FIXED64: pa.uint64(),
        FieldDescriptor.TYPE_FIXED32: pa.uint32(),
        FieldDescriptor.TYPE_BOOL: pa.bool_(),
        FieldDescriptor.TYPE_STRING: pa.string(),
        FieldDescriptor.TYPE_BYTES: pa.binary(),
        FieldDescriptor.TYPE_UINT32: pa.uint32(),
        FieldDescriptor.TYPE_ENUM: pa.string(),
        FieldDescriptor.TYPE_SFIXED32: pa.int32(),
        FieldDescriptor.TYPE_SFIXED64: pa.int64(),
        FieldDescriptor.TYPE_SINT32: pa.int32(),
        FieldDescriptor.TYPE_SINT64: pa.int64(),
    }
    return type_mapping.get(field.type, pa.null())


def protobuf_objects_to_pyarrow_table(proto_objects: List[Any]) -> pa.Table:
    if not proto_objects:
        raise ValueError("The list of protobuf objects is empty.")

    # Extract schema from the first protobuf object
    message_descriptor = type(proto_objects[0]).DESCRIPTOR
    schema = protobuf_to_pyarrow_schema(message_descriptor)

    data = []
    for msg in proto_objects:
        cur_obj = {}
        for field in schema:
            field_name = field.name
            cur_obj[field_name] = extract_field_data(msg, field)
        data.append(cur_obj)

    table = pa.Table.from_pylist(data, schema=pa.schema(schema))
    return table


def _get_attr(field: str, msg):
    atr = getattr(msg, field, None) if msg else None
    if atr is not None:
        field_descriptor = msg.DESCRIPTOR.fields_by_name[field]
        if (
            not field_descriptor.message_type
        ) and field_descriptor.type == field_descriptor.TYPE_ENUM:
            atr = _get_enum_name(atr, field_descriptor)
    return atr


def _safe_get_attr(field: str, data: Any) -> Any:
    return _get_attr(field, data) if data else None


@cache
def _get_enum_name(enum_value, field_descriptor):
    # Get the enum descriptor
    enum_descriptor = field_descriptor.enum_type

    # Get the enum name using the descriptor
    enum_name = enum_descriptor.values_by_number[enum_value].name
    return enum_name


def extract_field_data(msg, field) -> Any:
    is_nested = False
    cur_msg = msg
    for part in field.name.split("."):
        if is_nested:
            potential_descriptors = [
                inner_msg.DESCRIPTOR for inner_msg in cur_msg if inner_msg is not None
            ]
            descriptor = (
                potential_descriptors[0].fields_by_name[part]
                if potential_descriptors
                else None
            )
        else:
            descriptor = cur_msg.DESCRIPTOR.fields_by_name[part]

        if descriptor is None:
            return None

        if is_nested and (descriptor.label == descriptor.LABEL_REPEATED):
            raise ValueError("Cannot parse multi-nested repeating fields.")
        elif is_nested:
            cur_msg = [_safe_get_attr(part, msg_val) for msg_val in cur_msg]
        elif descriptor.label == descriptor.LABEL_REPEATED:
            is_nested = True
            cur_msg = _safe_get_attr(part, cur_msg)
        else:
            cur_msg = _safe_get_attr(part, cur_msg)

    return cur_msg
