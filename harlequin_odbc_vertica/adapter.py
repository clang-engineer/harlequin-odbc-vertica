from __future__ import annotations

from typing import Any, Sequence

from harlequin import HarlequinAdapter, HarlequinCursor
from harlequin_odbc.adapter import HarlequinOdbcAdapter, HarlequinOdbcConnection

from harlequin_odbc.catalog import (
    DatabaseCatalogItem as OdbcDatabaseCatalogItem,
    RelationCatalogItem,
    SchemaCatalogItem,
)
from harlequin_odbc.cli_options import ODBC_OPTIONS
from harlequin.catalog import Catalog, CatalogItem
from harlequin.exception import HarlequinConnectionError

import pyodbc


class DatabaseCatalogItem(OdbcDatabaseCatalogItem):
    """A Vertica database node without unsupported database actions."""

    INTERACTIONS = None


class HarlequinOdbcVerticaConnection(HarlequinOdbcConnection):
    """ODBC Connection with Vertica catalog fixes."""

    def _list_tables(self) -> dict[str, dict[str, list[tuple[str, str]]]]:
        cur = self.aux_conn.cursor()
        catalog: dict[str, dict[str, list[tuple[str, str]]]] = {}
        default_db: str | None = None

        for db_name, schema_name, rel_name, rel_type, *_ in cur.tables(catalog="%"):
            if db_name is None:
                if default_db is None:
                    cur2 = self.aux_conn.cursor()
                    cur2.execute("SELECT current_database()")
                    default_db = cur2.fetchone()[0]
                db_name = default_db

            if db_name not in catalog:
                catalog[db_name] = dict()

            if schema_name is None:
                continue
            if schema_name not in catalog[db_name]:
                catalog[db_name][schema_name] = list()

            if rel_name is not None:
                catalog[db_name][schema_name].append((rel_name, rel_type or ""))

        return catalog

    def _list_columns_in_relation(
        self, catalog_name: str, schema_name: str, rel_name: str
    ) -> list[tuple[str, str]]:
        cur = self.aux_conn.cursor()
        raw_cols = cur.columns(table=rel_name, schema=schema_name)
        return [(col[3], col[5]) for col in raw_cols]

    def get_catalog(self) -> Catalog:
        raw_catalog = self._list_tables()
        db_items: list[CatalogItem] = []
        for db, schemas in raw_catalog.items():
            schema_items: list[CatalogItem] = []
            for schema, relations in schemas.items():
                rel_items = [
                    RelationCatalogItem.from_label(
                        label=rel,
                        schema_label=schema,
                        db_label=db,
                        rel_type=rel_type,
                        connection=self,
                    )
                    for rel, rel_type in relations
                ]
                schema_items.append(
                    SchemaCatalogItem.from_label(
                        label=schema,
                        db_label=db,
                        connection=self,
                        children=rel_items,
                    )
                )
            db_items.append(
                DatabaseCatalogItem.from_label(
                    label=db,
                    connection=self,
                    children=schema_items,
                )
            )
        return Catalog(items=db_items)


class HarlequinOdbcVerticaAdapter(HarlequinOdbcAdapter):
    """ODBC adapter with Vertica catalog fixes."""

    ADAPTER_OPTIONS = ODBC_OPTIONS

    def __init__(self, conn_str: Sequence[str], **_: Any) -> None:
        super().__init__(conn_str, **_)

    def connect(self) -> HarlequinOdbcVerticaConnection:
        conn = HarlequinOdbcVerticaConnection(self.conn_str)
        return conn
