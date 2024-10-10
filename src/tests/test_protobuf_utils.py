import pyarrow as pa
from google.protobuf import descriptor_pb2
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.message_factory import GetMessageClass

from src.normalize.protobuf_utils import protobuf_to_pyarrow_schema, \
    protobuf_objects_to_pyarrow_table


# Create Protobuf message descriptors
def create_file_descriptor():
    file_descriptor = descriptor_pb2.FileDescriptorProto()
    file_descriptor.name = "test.proto"
    file_descriptor.package = "test"

    person = file_descriptor.message_type.add()
    person.name = "Person"

    person.field.add(name="name", number=1, type=FieldDescriptor.TYPE_STRING)
    person.field.add(name="age", number=2, type=FieldDescriptor.TYPE_INT32)

    address = person.nested_type.add()
    address.name = "Address"
    address.field.add(name="street", number=1,
                      type=FieldDescriptor.TYPE_STRING)
    address.field.add(name="city", number=2, type=FieldDescriptor.TYPE_STRING)

    person.field.add(name="addresses", number=3,
                     type=FieldDescriptor.TYPE_MESSAGE,
                     type_name=".test.Person.Address",
                     label=FieldDescriptor.LABEL_REPEATED)

    return file_descriptor


# Create message classes
fd = create_file_descriptor()
dp = DescriptorPool()
dp.Add(fd)

Person = GetMessageClass(dp.FindMessageTypeByName("test.Person"))
Address = GetMessageClass(dp.FindMessageTypeByName("test.Person.Address"))


def test_protobuf_to_pyarrow_schema():
    person_descriptor = dp.FindMessageTypeByName("test.Person")
    schema = protobuf_to_pyarrow_schema(person_descriptor)
    assert len(schema) == 4
    assert schema[0] == pa.field("name", pa.string())
    assert schema[1] == pa.field("age", pa.int32())
    assert schema[2] == pa.field("addresses.street", pa.list_(pa.string()))
    assert schema[3] == pa.field("addresses.city", pa.list_(pa.string()))


def test_protobuf_objects_to_pyarrow_table():
    # Create Protobuf objects
    person1 = Person()
    person1.name = "Alice"
    person1.age = 30
    address1 = person1.addresses.add()
    address1.street = "123 Main St"
    address1.city = "New York"
    address2 = person1.addresses.add()
    address2.street = "456 Elm St"
    address2.city = "Boston"

    person2 = Person()
    person2.name = "Bob"
    person2.age = 25
    address3 = person2.addresses.add()
    address3.street = "789 Oak St"
    address3.city = "Chicago"

    proto_objects = [person1, person2]

    table = protobuf_objects_to_pyarrow_table(proto_objects)

    assert isinstance(table, pa.Table)
    assert table.num_columns == 4
    assert table.num_rows == 2
    assert table.schema.names == ["name", "age", "addresses.street",
                                  "addresses.city"]
    assert table.column("name").to_pylist() == ["Alice", "Bob"]
    assert table.column("age").to_pylist() == [30, 25]
    assert table.column("addresses.street").to_pylist() == [
        ["123 Main St", "456 Elm St"], ["789 Oak St"]]
    assert table.column("addresses.city").to_pylist() == [
        ["New York", "Boston"], ["Chicago"]]


def test_nested_non_repeated_struct():
    file_descriptor = descriptor_pb2.FileDescriptorProto()
    file_descriptor.name = "nested_test.proto"
    file_descriptor.package = "nested_test"

    nested_person = file_descriptor.message_type.add()
    nested_person.name = "NestedPerson"
    nested_person.field.add(name="name", number=1,
                            type=FieldDescriptor.TYPE_STRING)
    nested_person.field.add(name="home_address", number=2,
                            type=FieldDescriptor.TYPE_MESSAGE,
                            type_name=".nested_test.NestedPerson.Address")

    address = nested_person.nested_type.add()
    address.name = "Address"
    address.field.add(name="street", number=1,
                      type=FieldDescriptor.TYPE_STRING)
    address.field.add(name="city", number=2, type=FieldDescriptor.TYPE_STRING)

    pool = DescriptorPool()
    pool.Add(file_descriptor)
    nested_person_descriptor = pool.FindMessageTypeByName(
        "nested_test.NestedPerson")

    schema = protobuf_to_pyarrow_schema(nested_person_descriptor)
    assert len(schema) == 3
    assert schema[0] == pa.field("name", pa.string())
    assert schema[1] == pa.field("home_address.street", pa.string())
    assert schema[2] == pa.field("home_address.city", pa.string())
