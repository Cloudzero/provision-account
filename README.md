# Provision Account

## Problem Statement

This repo provides full transparency to the resources CloudZero creates in your AWS accounts
when you onboard.


# Getting Started with Development

## Prep

You need the AWS CLI and AWS SAM Local CLI (for testing). You can install these on your own, or use the provided `Makefile`.

I suggest using a python virtual environment when installing the requirements. Once in your virtualenv, simply use `make init` to
install the needed CLI tools and dependencies. `I use `pyenv`, so my commands are:

```
pyenv activate watts
make clean
make init  # NOTE: this target will only work if you're _in_ a virtualenv
```


## Usage
