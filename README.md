# yams (YAML Params)

[![codecov](https://codecov.io/gh/marshall-lab/yams/branch/main/graph/badge.svg?token=IPaq8iFzsM)](https://codecov.io/gh/marshall-lab/yams)[![](https://github.com/marshall-lab/yams/workflows/Unit%20Tests/badge.svg)](https://github.com/marshall-lab/TITAN/actions)[![GitHub](https://img.shields.io/github/license/marshall-lab/yams)](https://github.com/marshall-lab/yams/blob/main/LICENSE)

yams is a parameter definition language and parser - all in yaml.

## Parameter Definition

The parameter definition language (PDL) provides expressions for defining input types, creation of types for the target application, and simple validation of input values.  The PDL itself is YAML and can be defined either in one file or a directory of yaml files.

**An example params definition:**
```yml
classes:
  animals:
    type: definition
    description: Animals included in model
    fields:
      goes:
        type: any
        description: What noise does the animal make?
        default: oink
      is_mammal:
        type: boolean
        description: Is this animal a mammal
        default: false
      friends_with:
        type: keys
        description: What animals does this animal befriend
    default:
      cat:
        goes: meow
        is_mammal: true
        friends_with:
          - cat
          - dog
      dog:
        goes: woof
        is_mammal: true
        friends_with:
          - dog
          - turtle
          - cat
      turtle:
        goes: gurgle
        friends_with:
          - dog
          - turtle
  locations:
    type: array
    description: Where do the animals go?
    default:
      - barn
      - ocean
    values:
      - barn
      - ocean
      - sky
      - woods

demographics:
  type: sub-dict
  description: "Parameters controlling population class level probabilities and behaviors"
  keys:
    - animals
    - locations
  default:
    num:
      type: int
      default: 10
      description: Number of animals of this type at this location
    prob_happy:
      type: float
      default: 1.0
      description: Probability an animal is happy
      min: 0.0
      max: 1.0
    color:
      type: enum
      default: blue
      description: What's the color of this animal/location combo
      values:
        - blue
        - indigo
        - cyan

neighbors:
  type: definition
  description: Definition of an edge (relationship) between two locations
  fields:
    location_1:
      type: enum
      default: barn
      class: locations
    location_2:
      type: enum
      default: sky
      class: locations
    distance:
      type: float
      default: 0
      min: 0
  default:
    edge_default:
      location_1: barn
      location_2: sky
      distance: 1000

```

Parameters are defined as key value pairs (typically nested).  There are some reserved keys that allow for definition of a parameter item, but otherwise a key in the parameter definition is interpreted as an expected key in the parameters.

The reserved keys used for defining parameters are:
* `type`
* `default`
* `description`
* `min`
* `max`
* `values`
* `fields`

Specifically, if the `default` key is present in a yaml object, then that object will be interpreted as a parameter definition.  The other keys are used in that definition

For example, in the below `type` is used as a parameter key, which is allowed (though perhaps not encouraged for readability reasons) as `default` is not a key at the same level of `type`.  The second usage of `type` is interpreted as the definition of `type` (the key) being an `int`.

```yml
a:
  type:
    type: int
    default: 0
    description: the type of a
```

`classes` is also reserved as a root key (see [using classes](#using-classes) below)

### Required Keys

Every parameter item must have the `type`, and `default` keys (`description` highly encouraged, but not required).

See [#types] for more information on the types and how they interact with the other keys.

The `default` key should be a valid value given the rest of the definition.  The `default` key can include parameter definitions within it.  This is common with `sub-dict` param definitions.

The `description` is a free text field to provide context for the parameter item.  This can also be used to generate documentation (no automated support at this time - see [TITAN's params app](https://github.com/marshall-lab/titan-params-app) as an example).

### Types

The `type` of a parameter definition dictates which other fields are required/used when parsing the definition.

#### `int`

The value of the parameter is expected to be an integer.

Required keys:
* None

Optional keys:
* `min` - the minimum value (inclusive) this parameter can take
* `max` - the maximum value (inclusive) this parameter can take

Example definition:
```yml
fav_num:
  type: int
  default: 12
  description: a is your favorite 3-or-fewer-digit number
  min: -999
  max: 999
```

Example usage:
```yml
fav_num: 13
```

#### `float`

The value of the parameter is expected to be a floating point number

Required keys:
* None

Optional keys:
* `min` - the minimum value (inclusive) this parameter can take
* `max` - the maximum value (inclusive) this parameter can take

Example definition:
```yml
heads_prob:
  type: float
  default: 0.5
  description: the probability heads is flipped
  min: 0.0
  max: 1.0
```

Example usage:
```yml
heads_prob: 0.75
```

#### `boolean`

The value of the parameter is expected to be a true/false value

Required keys:
* None

Optional keys:
* None

Example definition:
```yml
use_feature:
  type: boolean
  description: whether or not to use this feature
  default: false
```

Example usage:
```yml
use_feature: true
```

#### `array`

The value of the parameter is expected to be an array of values selected from the defined list.

Required keys:
* `values` - either a list of strings that the parameter can take, or the name of a class whose values can be used

Optional keys:
* None

Example definition:
```yml
locations:
  type: array
  description: Where do the animals go?
  default:
    - barn
    - ocean
  values:
    - barn
    - ocean
    - sky
    - woods
```

Example usage:
```yml
locations:
  - sky
  - ocean
```

#### `enum`

The value of the parameter is expected to be a single value selected from the defined list.

Required keys:
* `values` - either a list of strings that the parameter can take, or the name of a class whose values can be used

Optional keys:
* None

Example definition:
```yml
classes:
  my_classes:
    type: array
    description: which class my params has
    default:
      - a
      - b
    values:
      - a
      - b
      - c

affected_class:
  type: enum
  default: a
  description: which class is affected by this feature
  values: my_classes
```

Example usage:
```yml
my_classes:
  - b
  - c

affected_class: c
```

#### `any`

The value of the parameter can take on any value and will not be validated.

Required keys:
* None

Optional keys:
* None

Example definition:
```yml
name:
  type: any
  description: what is your name?
  default: your name here
```

Example usage:
```yml
name: yams
```

#### `bin`

Binned (integer) keys with set value fields.

Required keys:
* `fields` - parameter definitions for each required field in the binned items.  Because the sub-fields of a bin are required, no default can be provided.


Optional keys:
* None

Example definition:
```yml
bins:
  type: bin
  description: "Binned probabilities of frequencies"
  fields:
    prob:
      type: float
      min: 0.0
      max: 1.0
    min:
      type: int
      min: 0
    max:
      type: int
      min: 0
  default:
    1:
      prob: 0.585
      min: 1
      max: 6
    2:
      prob: 0.701
      min: 7
      max: 12
    3:
      prob: 0.822
      min: 13
      max: 24
```

Example usage:
```yml
bins:
  1:
    prob: 0.5
    min: 0
    max: 10
  2:
    prob: 0.9
    min: 11
    max: 20
```

#### `sub-dict`

Build a set of params for each key combination listed.  Requires use of `classes` root key.  The default should contain parameter definition items.  Can facet on up to two classes.

Required keys:
* `keys` - which params under the `classes` root key should be sub-dicted off of

Optional keys:
* None

Example definition:
```yml
classes:
  my_classes:
    type: array
    description: which class my params has
    default:
      - a
      - b
    values:
      - a
      - b
      - c

demographics:
  type: sub-dict
  description: parameters defining characteristics of each class
  keys:
    - my_classes
  default:
    num:
      type: int
      default: 0
      description: number of agents in the class
```

Example usage:
```yml
demographics:
  a:
    num: 10
  b:
    num: 20
```

#### `definition`

Define an item with the given interface.

Required keys:
* `fields` - the fields defining the interface for each defined item.  Each field is a param definition item.

Optional keys:
* None

Example definition:
```yml
animals:
  type: definition
  description: Animals included in model
  fields:
    goes:
      type: any
      description: What noise does the animal make?
      default: oink
    is_mammal:
      type: boolean
      description: Is this animal a mammal
      default: false
    friends_with:
      type: keys
      desciption: What animals does this animal befriend
  default:
    cat:
      goes: meow
      is_mammal: true
      friends_with:
        - cat
        - dog
    dog:
      goes: woof
      is_mammal: true
      friends_with:
        - dog
        - cat
```

Example usage:
```yml
animals:
  sheep:
    goes: bah
    is_mammal: true
  pig:
    is_mammal: true
  fish:
    goes: glugglug
```

### Using Classes

The `classes` key as a root key of the parameter definitions takes on special meaning.  The parameters chosen in this section can be used to determine acceptable values in other sections of the params (via `enum` and `array` types), or to determine what params need to be created (via `sub-dict` type).
