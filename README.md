# Cooper Control Tool

[![Travis](https://img.shields.io/travis/hardwario/cpctl/master.svg)](https://travis-ci.org/hardwario/cpctl)
[![Release](https://img.shields.io/github/release/hardwario/cpctl.svg)](https://github.com/hardwario/cpctl/releases)
[![License](https://img.shields.io/github/license/hardwario/cpctl.svg)](https://github.com/hardwario/cpctl/blob/master/LICENSE)

This is the CLI tool to control cooper

## Installing

You can install **cpctl** directly from PyPI:


```sh
    sudo pip3 install -U cpctl
```

> Note: You may need to use `sudo` before the command - it depends on the operating system used...

## Usage

This tool has built-in help system. Just run:

```sh
>> cpctl --help
Usage: cpctl [OPTIONS] COMMAND [ARGS]...

  Cooper Control Tool.

Options:
  --version          Show the version and exit.
  -d, --device TEXT  Device path.
  --help             Show this message and exit.

Commands:
  config   Config
  devices  Print available devices.
  node     Manage the nodes

```

## License

This project is licensed under the [**MIT License**](https://opensource.org/licenses/MIT/) - see the [**LICENSE**](LICENSE) file for details.
