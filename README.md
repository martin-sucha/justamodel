# Simple python model definition

- Just a model definition and validation
- Python3 only
- preserves declaration order of the fields
- Supports model inheritance
- Supports polymorphic model types
- Convert a model tree to/from dict, but independent of how fields are represented when serialized


## Installation

```python
pip install justamodel
```

## Basic example

```python
from justamodel.model import Model, Field
from justamodel.types import StringType, IntType, ListType, ModelType


class Fruit(Model):
    name = Field(StringType(min_length=1))
    colour = Field(StringType(), required=False)
    pieces = Field(IntType(), default=2)


Fruit.fields  # an OrderedDict of justamodel.Field in Fruit model

Fruit()
# Fruit(name='', colour=None, pieces=2)

    
class Bowl(Model):
    location = Field(StringType())
    contents = Field(ListType(ModelType(Fruit)))


Bowl()  # Bowl(location='', contents=[])

bowl = Bowl(
        location='dining room',
        contents=[Fruit(name='apple', colour='red', pieces=3), Fruit(name='banana', pieces=1)]
       )

bowl  # Bowl(location='dining room', contents=[Fruit(name='apple', colour='red', pieces=3), Fruit(name='banana', colour=None, pieces=1)])
bowl.location  # 'dining room'

bowl.validate()  # no exception

bowl.location = None
bowl.validate()  # justamodel.exceptions.ModelValidationError
```

## Convert to/from dict

```python
bowl.location='kitchen'
from justamodel.serializer import DictModelSerializer

serializer = DictModelSerializer()
data = serializer.serializer_model(bowl)
# {'contents': [Fruit(name='apple', colour='red', pieces=3), Fruit(name='banana', colour=None, pieces=1)], 'location': 'kitchen'}

serializer.deserialize(data, Bowl)
# Bowl(location='kitchen', contents=[Fruit(name='apple', colour='red', pieces=3), Fruit(name='banana', colour=None, pieces=1)])

```

## Model inheritance

```python
class ColouredBowl(Bowl):
  colour = Field(StringType(min_length=1))

bowl2 = ColouredBowl(location='kitchen', colour='red', contents=[])
bowl2  # ColouredBowl(location='kitchen', contents=[], colour='red')

```

## Polymorphic models

```python

class Bag(Model):
  owner = Field(StringType())

from justamodel.model import PolymorphicModel

class Container(PolymorphicModel):
  types_to_model_classes = {
    'bowl': Bowl,
    'coloured_bowl': ColouredBowl,
    'bag': Bag
  }


# Polymorphic models have a subclass hook
issubclass(Bowl, Container)  # True
issubclass(ColouredBowl, Container)  # True
issubclass(Bag, Container)  # True


data_a = serializer.serialize_model(bowl, Container)
# {'type': 'bowl', 'contents': [Fruit(name='apple', colour='red', pieces=3), Fruit(name='banana', colour=None, pieces=1)], 'location': 'kitchen'}

data_b = serializer.serialize_model(bowl2, Container)
# {'type': 'coloured_bowl', 'contents': [], 'colour': 'red', 'location': 'kitchen'}

data_c = serializer.serialize_model(Bag(owner='me'), Container)
# {'type': 'bag', 'owner': 'me'}

serializer.deserialize_model(data_a, Container)
# Bowl(location='kitchen', contents=[Fruit(name='apple', colour='red', pieces=3), Fruit(name='banana', colour=None, pieces=1)])

serializer.deserialize_model(data_b, Container)
# ColouredBowl(location='kitchen', contents=[], colour='red')

serializer.deserialize_model(data_c, Container)
# Bag(owner='me')
```
