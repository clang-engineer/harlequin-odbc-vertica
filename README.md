# harlequin-odbc-vertica

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

```bash
pip install harlequin-odbc-vertica
```

Or with `uv`:

```bash
uv tool install harlequin --with harlequin-odbc-vertica
```

### Prerequisites

You need:

- [Harlequin](https://harlequin.sh) installed
- An ODBC driver manager (`unixodbc` on macOS/Linux)
- The [Vertica ODBC driver](https://www.vertica.com/download/vertica/odbc-driver/) installed and registered in `odbcinst.ini`

## Usage

```bash
harlequin -a odbc-vertica 'DRIVER={Vertica};SERVER=your-server;PORT=5433;DATABASE=your-db;UID=user;PWD=password'
```

## License

MIT
