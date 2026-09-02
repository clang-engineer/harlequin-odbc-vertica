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
