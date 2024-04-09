# konfig

## Key Organizer for Numerous Functionalities and Intricate Gearings

Konfig is a simple yet effective configuration manager inspired by Python dataclasses.

### Installation

```bash
pip install https://github.com/kenichdietrich/konfig.git
```

### Usage

```python
from Konfig import Konfig, default
```

Just inherit Konfig and set your config parameters as class attributes, as if you were defining a dataclass

```python
class ConfigA(Konfig):
    num_iterations: int = 1_000
    """number of training iterations"""
    layers: list[int] = default([128, 128, 4])
    """number of hidden units for each layer"""
```

For mutable default values (lists, class instances, etc) you must wrap them with the default function. Then, create an instance with custom values

```python
config_a = ConfigA(num_iterations=500)

config_a.num_iterations # 500
config_a.layers # [128, 128, 4]
```

You can export the configuration parameters to a TOML file

```python
config_a.to_toml("my_config.toml")
```

read again

```python
config_a = ConfigA.from_toml("my_config.toml")
```

and print in console

```python
config_a.print()

# output:
# num_iterations = 500
# layers = [ 128, 128, 4,]
```

It is even possible to nest Konfigs

```python
class ConfigB(Konfig):
    """hello my friend"""

    layers: list[int] = default([128, 64, 64])
    """number of hidden units for each layer"""
    num_iterations: int = 2_000
    """number of training iterations"""
    config_a: ConfigA = default(ConfigA())
    """other config"""
    other_param: float = 9.0
    """other"""
```

and proceed in the same way

```python
config_b = ConfigB(other_param=2.1, config_a=ConfigA(layers=[64, 32]))

config_b.other_param # 2.1
config_b.config_a.layers # [64, 32]

config_a.print()

# output:
# layers = [ 128, 64, 64,]
# num_iterations = 2000
# other_param = 2.1

# [config_a]
# num_iterations = 1000
# layers = [ 64, 32,]
```

Not only that, but using a Konfig class as an entrypoint in a CLI is as easy as

```python
# my_script.py

config_b = ConfigB.cli(description="config parameters for my script")
```

```bash
python3 my_script.py --help
```

```
usage: myscript.py [-h] [--layers  [...]] [--num-iterations] [--config_a.num-iterations] [--config_a.layers  [...]] [--other-param] [--template] [--from-toml]

config parameters for my script

options:
  -h, --help            show this help message and exit
  --layers  [ ...]      number of hidden units for each layer (default=[128, 64, 64])
  --num-iterations      number of training iterations (default=2000)
  --config_a.num-iterations 
                        number of training iterations (default=1000)
  --config_a.layers  [ ...]
                        number of hidden units for each layer (default=[128, 128, 4])
  --other-param         other (default=9.0)
  --template            generates a toml template file
  --from-toml           load toml file from path
```

Note that the comments under the parameters in the definition are used as descriptors. If you prefer to enter config params via toml file you can generate a template with the `--template` option and load it with the `--from-toml` argument.

```bash
python3 my_script.py --template # generates ./ConfigB.toml

# edit by hand...

python3 my_script.py --from-toml ConfigB.toml
```