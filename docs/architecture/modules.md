# Modular repository layout

The project uses a modular repository strategy inspired by PipePipe's use of Git submodules.

## Current state

The web client and its boundaries are folders in this repository. There are no submodules yet.

## When to extract a module

Create a standalone repository only when a module has a stable responsibility, documented public interface, tests, and a clear maintenance and license policy.

## Adding a submodule later

After the standalone repository exists, add it with a reviewed command similar to:

```bash
git submodule add https://github.com/Lanzkila/REPOSITORY.git modules/MODULE
git commit -m "build: add MODULE submodule"
```

Pin submodules to reviewed commits. Avoid tracking floating branches for production builds unless an explicit update workflow is provided.
