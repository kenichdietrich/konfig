import inspect, argparse, typing, sys
from dataclasses import dataclass, field, MISSING
from pathlib import Path

import toml


def default(obj):
    if callable(obj):
        return field(default_factory=obj)
    return field(default_factory=lambda: obj)


def is_konfig(obj):
    if isinstance(obj, type):
        return issubclass(obj, Konfig)
    return isinstance(obj, Konfig)


def _get_comments(cls):
    source_code = inspect.getsource(cls)
    lines = [l.strip() for l in source_code.split("\n")]
    comments = {}
    for k, v in cls.__annotations__.items():
        if is_konfig(v):
            comments[k] = _get_comments(v)
        else:
            for i, l in enumerate(lines):
                if l.startswith(f"{k}:") and i + 1 < len(lines):
                    next_l = lines[i + 1]
                    if next_l.startswith(("'''", '"""')):
                        comments[k] = next_l.strip('"').strip("'")
                    continue
    return comments


def _get_annotations(cls):
    annotations = cls.__annotations__.copy()
    for k, v in cls.__annotations__.items():
        if is_konfig(v):
            annotations[k] = _get_annotations(v)
    return annotations


def _get_default_values(obj):
    values = {}
    for k, v in obj.__annotations__.items():
        if is_konfig(v):
            values[k] = _get_default_values(v)
        else:
            _field = obj.__dataclass_fields__[k]
            if _field.default is not MISSING or _field.default_factory is not MISSING:
                values[k] = (
                    _field.default
                    if _field.default is not MISSING
                    else _field.default_factory()
                )
    return values


def _get_cli_config(cls, prefix: str = None):
    cli_config = {}
    for k, v in cls.__annotations__.items():
        if is_konfig(v):
            config = _get_cli_config(v, k)
            cli_config = cli_config | config
        else:
            config = {"help": cls._comments.get(k) or "", "type": v, "metavar": ""}
            default_value = cls._default_values.get(k)
            if default_value is not None:
                config["default"] = default_value
                config["help"] += f" (default={default_value})"
            if typing.get_origin(v) is list:
                config["nargs"] = "+"
                config["type"] = typing.get_args(v)[0]
            name = k.replace("_", "-")
            cli_config[f"{prefix}.{name}" if prefix else name] = config
    return cli_config


def _initialize_with_dict(cls, args_dict: dict):
    kwargs = args_dict.copy()
    for k, v in cls.__annotations__.items():
        if is_konfig(v):
            sub_args = args_dict[k]
            kwargs[k] = _initialize_with_dict(v, sub_args)
    return cls(**kwargs)


def _cli_args_to_args_dict(cli_args: dict):
    def insert(_dict, keys, value):
        for k in keys[:-1]:
            _dict = _dict.setdefault(k, {})
        _dict[keys[-1]] = value

    args_dict = {}
    for k, v in cli_args.items():
        keys = k.split(".")
        insert(args_dict, keys, v)
    return args_dict


def _initialize_with_cli(cls, cli_args: dict):
    args_dict = _cli_args_to_args_dict(cli_args)
    return _initialize_with_dict(cls, args_dict)


def _to_dict(obj) -> dict:
    config_dict = vars(obj).copy()
    for k, v in config_dict.items():
        if is_konfig(v):
            config_dict[k] = _to_dict(v)
    return config_dict


class Konfig:
    def __init_subclass__(cls):
        dataclass(cls)
        cls.__doc__ = cls.__name__ + str(inspect.signature(cls)).replace(" -> None", "")
        cls._comments = _get_comments(cls)
        cls._annotations = _get_annotations(cls)
        cls._default_values = _get_default_values(cls)

    def print(self):
        print(self._to_toml_str())

    def to_dict(self):
        return _to_dict(self)

    def _to_toml_str(self):
        return toml.dumps(self.to_dict())

    def to_toml(self, path: typing.Union[str, Path]):
        toml_str = self._to_toml_str()
        Path(path).write_text(toml_str)

    @classmethod
    def from_toml(cls, path: typing.Union[str, Path]):
        toml_args = toml.loads(Path(path).read_text())
        return _initialize_with_dict(cls, toml_args)

    @classmethod
    def cli(cls, command: str = None, description: str = None, save_toml: bool = False):
        parser = argparse.ArgumentParser(
            prog=command, description=description or f"{cls.__name__}"
        )
        cli_args_config = _get_cli_config(cls)
        for k, kwargs in cli_args_config.items():
            parser.add_argument("--" + k, **kwargs)
        parser.add_argument(
            "--template",
            help="generates a toml template file",
            action="store_true",
        )
        parser.add_argument(
            "--from-toml",
            help="load toml file from path",
            type=str,
            default="",
            metavar="",
        )

        args = vars(parser.parse_args())
        template = args.pop("template")
        from_toml = args.pop("from_toml")

        if from_toml:
            return cls.from_toml(from_toml)

        config = _initialize_with_cli(cls, args)
        if save_toml or template:
            config.to_toml(f"{cls.__name__}.toml")
        if template:
            sys.exit()

        return config
