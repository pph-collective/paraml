# paraml (Param YAML)

[![codecov](https://codecov.io/gh/marshall-lab/paraml/branch/main/graph/badge.svg?token=IPaq8iFzsM)](https://codecov.io/gh/marshall-lab/paraml) [![](https://github.com/marshall-lab/paraml/workflows/Unit%20Tests/badge.svg)](https://github.com/marshall-lab/paraml/actions) [![GitHub](https://img.shields.io/github/license/marshall-lab/paraml)](https://github.com/marshall-lab/paraml/blob/main/LICENSE) [![PyPI version](https://badge.fury.io/py/paraml.svg)](https://pypi.org/project/paraml/)

paraml is a parameter definition language and parser - all in yaml.

## Table of Contents

*Note:* README internal links only work on [GitHub](https://github.com/marshall-lab/paraml)

1. [Motivation](#motivation)
2. [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Running paraml](#running-paraml)
3. [Parameter Definition](#parameter-definition)
    - [Required Keys](#required-keys)
    - [Types](#types)
    - [Using Classes](#using-classes)

## Motivation
paraml is a spinoff from [TITAN](https://github.com/marshall-lab/TITAN), an agent based model.  We have many parameters in that model, many of which are not used in a given run. paraml addresses the following pain points we had:

* Parameters often weren't formally defined/described anywhere - some had comments, some were hopefully named idiomatically. This caused issues onboarding new people to using the model.
* Parameters were statically defined/hard coded, but often we wanted them to be dynamic.
* Parameters needed to be filled out/defined by non-technical researchers - shouldn't need to know how to code to create a parameter file.
* Parameters need to have specific validation (e.g. a probability should be between 0 and 1, only `a` or `b` are expected values for parameter `y`), this was typically a run time failure - sometimes silent, sometimes explosive.
* If a user isn't using a feature of the model, they shouldn't have to worry about/carry around its parameters.
* Reproducibility of the run is key - must be able to re-run the model with the same params.
* We needed to be able to create common settings which described a specific world the model runs in and let users use those, but also override parameters as they needed for their run of the model.

How paraml addresses these:
* Parameter definitions require defaults
* Can add descriptions of parameters inline
* A small type system allows validation of params, as well as flexibility to define interfaces for params
* Parameter files only need to fill in what they want different from the defaults
* Can save off the fully computed params, which can then be re-used at a later date
* Can layer different parameter files, allowing more complex defaults and re-use of common scenarios

## Getting Started

### Installation

```
pip install paraml
```

### Running paraml

The entrypoint for running paraml is `paraml.create_params`.  This takes the parameter definitions, parameter files, and some options and returns a dictionary of the validated and computed parameters.

**Args:**
  * `def_path`: A yaml file or directory of yaml files containing the parameter definitions (see [Parameter Definition](#parameter-definition)).
  * `*param_paths`: The remaining args are interpreted as parameter files.  They will be merged in order (last merged value prevails).
  * `out_path`: Optional, if passed, save the computed parameters as a yaml to this location.
  * `error_on_unused`: Optional, if `True` throw an exception if there are parameters in `param_paths` that do not have a corresponding definition in the `def_path` definitions.

**Returns:**
 * A dictionary representing the parsed parameters.


**Example usage:**
```python
from paraml import create_params

def_path = "my/params/dir" # directory of the params definition files
base_params = "base/params.yaml" # file location of the first params
setting_param = "settings/my_setting" # directory of the second params files
intervention_params = "intervention/params" # directory of the third params files
out_path = "./params.yml" # location to save computed params to

params = create_params(
  def_path,
  base_params,
  setting_params,
  intervention_params,
  out_path=out_path,
  error_on_unused=True # if parameters are passed, but don't exist in the definition file, error
)
```


## Parameter Definition

The parameter definition language (PDL) provides expressions for defining input types, creation of types for the target application, and simple validation of input values.  The PDL itself is YAML and can be defined either in one file or a directory of yaml files. There can be multiple root keys in the parameter definition to namespace parameters by topic, and parameter definitions can be deeply nested for further organization of the params.  Only the `classes` key at the root of the definitions has special meaning (see [Using Classes](#using-classes)).

**An example params definition:**
```yml
# classes is a special parameter key that allows the params defined as sub-keys
# to be used in definitions for other sections
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
    description: Where do the animals live?
    default:
      - barn
      - ocean
    values:
      - barn
      - ocean
      - sky
      - woods

# demographics is another root-level parameter, which facets off of the values in classes
# then has parameter definitions for each of those combinations
demographics:
  type: sub-dict
  description: "Parameters controlling population class level probabilities and behaviors"
  keys:
    - animals
    - locations
  default:
    num:
      type: int
      default: 0
      description: Number of animals of this type at this location
    prob_happy:
      type: float
      default: 1.0
      description: Probability an animal is happy
      min: 0.0
      max: 1.0
    flag: # parameter definitions can be nested in intermediate keys to group related items
      color:
        type: enum
        default: blue
        description: What's the color is the flag of this animal/location combo
        values:
          - blue
          - indigo
          - cyan
      name:
        type: any
        default: animal land
        description: What is the name of this animal/location combo's flag

# neighbors is another root-level parameter
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

**An example of parameters for the definition above**
```yml
classes:
  animals:
    pig: # doesn't need a `goes` key as the default is oink and that is appropriate
      is_mammal: true
      friends_with:
        - pig
    fish: # fish don't need to specify `is_mammal` as false as that is the default
      goes: glugglug
      friends_with:
        - fish
    wolf:
      goes: ooooooooo
      is_mammal: true
      friends_with:
        - pig
  locations:
    - ocean
    - woods
    - barn

# the calculated params will fill in the default values for combinations of
# animals/colors/parameters that aren't specified below
demographics:
  pig:
    barn:
      num: 20
      flag:
        color: cyan
        name: piney porcines
  wolf:
    woods:
      num: 1
      prob_happy: 0.8
      flag:
        name: running solo
  fish:
    ocean:
      num: 1000001
      prob_happy: 0.4
      flag:
        color: indigo
        name: cool school

# we're defining a edges in a graph in this example, the names are labels for human readability only
neighbors:
  woodsy_barn:
    location_1: woods
    location_2: barn
    distance: 1
  woodsy_ocean:
    location_1: woods
    location_2: ocean
    distance: 3
  barn_ocean:
    location_1: barn
    location_2: ocean
    distance: 4
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

See [Types](#types) for more information on the types and how they interact with the other keys.

The `default` key should be a valid value given the rest of the definition.  The `default` key can include parameter definitions within it.  This is common with `sub-dict` param definitions.

The `description` is a free text field to provide context for the parameter item.  This can also be used to generate documentation (no automated support at this time - see [TITAN's params app](https://github.com/marshall-lab/titan-params-app) as an example).

### Types

The `type` of a parameter definition dictates which other fields are required/used when parsing the definition.

The types supported by paraml are:
* [`int`](#int)
* [`float`](#float)
* [`boolean`](#boolean)
* [`array`](#array)
* [`enum`](#enum)
* [`any`](#any)
* [`bin`](#bin)
* [`sub-dict`](#sub-dict)
* [`definition`](#definition)

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
name: paraml
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

Example class as value:
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
    default:
      cat:
        goes: meow
        is_mammal: true
      sheep:
        goes: baaaah
        is_mammal: true
  month:
    type: definition
    fields:
      mean_temp:
        type: float
        description: average temperature in °F
    default:
      april:
        mean_temp: 45.6

shearing:
  month:
    type: enum
    description: what season to shear animals
    class: month # This enum will only allow a value from the "month" class
    default: april
  to_shear:
    type: array
    description: which animals need to be sheared
    class: animal
    default:
      - sheep
```
Example usage of class as value:
```yml
classes:
  animals:
    sheep:
      goes: baaaah
      is_mammal: true
    cat:
      goes: meow
      is_mammal: true
    llama:
      goes: spits
      is_mammal: true
## we will only be using "april," which is the default month, so no definition needed!
shearing:
  month: april
  to_shear:
    - sheep
    - llama
```
