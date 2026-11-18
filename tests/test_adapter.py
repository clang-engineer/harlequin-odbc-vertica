from unittest import TestCase

from harlequin_odbc_vertica.adapter import (
    DatabaseCatalogItem,
    HarlequinOdbcVerticaConnection,
)


class GetCatalogTest(TestCase):
    def test_database_nodes_have_no_unsupported_interactions(self) -> None:
        connection = object.__new__(HarlequinOdbcVerticaConnection)
        connection._list_tables = lambda: {  # type: ignore[method-assign]
            "VERTICA": {"CDW": [("FT_CRE_APACHE", "TABLE")]}
        }

        catalog = connection.get_catalog()

        database = catalog.items[0]
        self.assertIsInstance(database, DatabaseCatalogItem)
        self.assertIsNone(database.INTERACTIONS)
        self.assertEqual(
            database.children[0].children[0].query_name,
            '"CDW"."FT_CRE_APACHE"',
        )


class ListTablesTest(TestCase):
    def test_missing_database_names_with_single_active_result(self) -> None:
        class SingleResultConnection:
            streaming_tables = False

            def cursor(self):
                return self

            def execute(self, query):
                if self.streaming_tables:
                    raise RuntimeError("Cannot query while SQLTables is active")
                return self

            def fetchone(self):
                return ("demo",)

            def tables(self, **kwargs):
                self.streaming_tables = True
                try:
                    yield (None, "public", "orders", "TABLE")
                    yield (None, "public", "order_summary", "VIEW")
                finally:
                    self.streaming_tables = False

        connection = object.__new__(HarlequinOdbcVerticaConnection)
        connection.aux_conn = SingleResultConnection()

        self.assertEqual(
            connection._list_tables(),
            {"demo": {"public": [("orders", "TABLE"), ("order_summary", "VIEW")]}},
        )
