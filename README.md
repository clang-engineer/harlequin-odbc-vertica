# harlequin-odbc-vertica

[![PyPI](https://img.shields.io/pypi/v/harlequin-odbc-vertica)](https://pypi.org/project/harlequin-odbc-vertica/)
[![CI](https://github.com/clang-engineer/harlequin-odbc-vertica/actions/workflows/ci.yml/badge.svg)](https://github.com/clang-engineer/harlequin-odbc-vertica/actions/workflows/ci.yml)

A [Harlequin](https://harlequin.sh) adapter for [Vertica](https://www.vertica.com/) via ODBC.

This adapter extends `harlequin-odbc` to fix Vertica-specific issues with catalog and column metadata retrieval.

## Problem

The standard `harlequin-odbc` adapter has two issues when used with Vertica:

1. **Empty Data Catalog**: Vertica's ODBC driver returns `None` for catalog names, causing all tables to be filtered out.
2. **Column listing error**: Vertica's ODBC driver does not support the `catalog` parameter in `SQLColumns`, resulting in `HYC00` errors.

## Solution

`harlequin-odbc-vertica` overrides two methods in the ODBC adapter:

- `_list_tables`: Uses `SELECT current_database()` as a fallback when the catalog name is `None`.
- `_list_columns_in_relation`: Omits the `catalog` parameter when calling `pyodbc.Cursor.columns()`.

## Installation

Three separate components are required:

1. **Harlequin and this Python plug-in**: `odbc-vertica` is the Harlequin
   adapter name. Installing the plug-in also installs its `harlequin-odbc` and
   `pyodbc` dependencies; it does **not** install a Vertica database driver.
2. **An ODBC driver manager**: unixODBC locates and loads registered native
   drivers. `odbcinst` is its configuration/query utility, not a driver.
3. **The native Vertica ODBC driver**: a separate library supplied by Vertica.
   It must be loadable by the driver manager and registered under the name
   `Vertica`, which matches `DRIVER={Vertica}` in the connection string.

### 1. Install Harlequin, unixODBC, and the plug-in

On macOS with Homebrew:

```sh
brew install harlequin unixodbc
```

On Debian/Ubuntu, install the driver manager with `sudo apt install unixodbc`;
install Harlequin using its [installation instructions](https://harlequin.sh/docs/getting-started).
Neither package manager command above installs the **native Vertica driver**.

Install this plug-in **in the same Python environment as Harlequin**. For a
virtual environment containing Harlequin:

```sh
python -m pip install harlequin-odbc-vertica
```

For a Homebrew-installed Harlequin, `pip` on your shell's `PATH` may point to
a different Python. Use the interpreter from Harlequin's entry-point script:

```sh
HARLEQUIN_PYTHON="$(head -n 1 "$(command -v harlequin)" | sed 's/^#!//')"
"$HARLEQUIN_PYTHON" -m pip install harlequin-odbc-vertica
```

If installing Harlequin as a `uv` tool instead:

```sh
uv tool install harlequin --with harlequin-odbc-vertica
```

After a Homebrew upgrade replaces Harlequin's environment, reinstall the
plug-in into the new environment. `harlequin --version` should list
`odbc-vertica` under installed adapters.

### 2. Install and register the native Vertica driver

Obtain the ODBC driver for your operating system from the
[Vertica client-driver installation documentation](https://docs.vertica.com/26.3.x/en/connecting-to/client-libraries/client-drivers/install-config/odbc/installing-odbc/).
Follow the vendor's installer instructions. On macOS, ensure the driver
library supports the architecture of the Python process running Harlequin:
an x86_64-only library cannot be loaded into an arm64 process.

```sh
odbcinst -j       # locations used by this unixODBC installation
odbcinst -q -d    # registered driver names; look for Vertica
```

If the vendor installer did not register `Vertica` with **this** unixODBC
installation, add an entry to the `odbcinst.ini` shown as `DRIVERS` by
`odbcinst -j`. Use the actual absolute path to the installed library (often
`.dylib` on macOS or `.so` on Linux), not the example below:

```ini
[Vertica]
Description = Vertica ODBC driver
Driver = /absolute/path/to/installed/vertica-odbc-library
FileUsage = 1
```

The `[Vertica]` section is the name referenced by `DRIVER={Vertica}`; the
`Driver` value is a filesystem path, **not** `harlequin-odbc-vertica`. A DSN
in `odbc.ini` is not required when passing a full connection string. After
registration, rerun `odbcinst -q -d` and check that the library path exists.
Listing a driver confirms its registration, not that it can load or connect.

## Usage

With a reachable Vertica server and valid credentials:

```sh
harlequin -a odbc-vertica 'DRIVER={Vertica};SERVER=your-server;PORT=5433;DATABASE=your-db;UID=user;PWD=your-password'
```

Real passwords in command-line arguments can appear in shell history and
process listings. For regular use, add a profile to a private Harlequin
config file (for example `~/.harlequin.toml`) instead:

```toml
[profiles.vertica]
adapter = "odbc-vertica"
conn_str = ["DRIVER={Vertica};SERVER=your-server;PORT=5433;DATABASE=your-db;UID=user;PWD=your-password"]
```

Replace the placeholders locally, restrict the file with
`chmod 600 ~/.harlequin.toml`, and launch with `harlequin -P vertica`.

## Troubleshooting

- **"Could not load an adapter named odbc-vertica"**: the plug-in is missing
  from the Python environment used by the `harlequin` executable. Check
  `harlequin --version` and reinstall into that environment as above.
- **`odbcinst -q -d` reports `SQLGetPrivateProfileString failed`**: inspect
  the `DRIVERS` path from `odbcinst -j`; no driver definitions may be
  available to this unixODBC installation. Install/register the native
  driver as described above.
- **"[unixODBC][Driver Manager] Can't open lib 'Vertica'"**: the native
  driver is missing, unregistered, or points to a library that cannot be
  loaded. Check `odbcinst -j`, `odbcinst -q -d`, the `Driver` path, and the
  library's architecture (`file /absolute/path/to/installed/library`).
- **Connection/authentication error after the driver loads**: check the
  server, port, database, credentials, and network access; registering a
  driver does not establish a database connection.
- **Empty catalog or column metadata errors with `-a odbc`**: use
  `-a odbc-vertica`, which applies the Vertica-specific metadata fixes.

## License

MIT
