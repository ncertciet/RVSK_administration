from typing import Dict, List, Any
from psycopg2 import sql
from psycopg2.extras import execute_values

from app.database.connection import get_connection, release_connection
from app.config.table_schema import TABLES
from app.config.settings import get_settings
from app.services.table_mapper import TableMapper
from app.utils.logger import logger

settings = get_settings()


class IngestionService:
    """
    Generic ingestion engine.

    Flow:
      Validate (done before calling)
      -> TableMapper
      -> Generic UPSERT
      -> Commit
    """

    def __init__(self):
        self.mapper = TableMapper()

    def ingest(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        conn = None
        cur = None
        summary = {}

        try:
            conn = get_connection()
            cur = conn.cursor()

            for record_chunk in self._chunks(records):
                mapped = self.mapper.split_records(record_chunk)

                for table_name, table_records in mapped.items():
                    if not table_records:
                        continue

                    self._bulk_upsert(cur, table_name, table_records)
                    summary[table_name] = (
                        summary.get(table_name, 0) + len(table_records)
                    )

            conn.commit()
            logger.info("Transaction committed successfully.")
            return summary

        except Exception as ex:
            if conn is not None:
                conn.rollback()
            logger.exception(ex)
            raise

        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                release_connection(conn)

    def _chunks(self, records: List[Dict[str, Any]]):
        chunk_size = max(1, settings.CHUNK_SIZE)

        for index in range(0, len(records), chunk_size):
            yield records[index:index + chunk_size]

    def _bulk_upsert(self, cursor, table_name: str, rows: List[Dict]):

        config = TABLES[table_name]

        columns = config["columns"]
        pk = config["primary_key"]

        if isinstance(pk, str):
            pk = [pk]

        update_columns = [
            c for c in columns
            if c not in pk
        ]

        update_sql = sql.SQL(",").join(
            sql.SQL("{column}=EXCLUDED.{column}").format(
                column=sql.Identifier(column)
            )
            for column in update_columns
        )

        query = sql.SQL("""
        INSERT INTO {table}
        ({columns})
        VALUES %s
        ON CONFLICT ({conflict_columns})
        DO UPDATE SET
        {updates}
        """).format(
            table=sql.Identifier("administration", table_name),
            columns=sql.SQL(",").join(
                sql.Identifier(column)
                for column in columns
            ),
            conflict_columns=sql.SQL(",").join(
                sql.Identifier(column)
                for column in pk
            ),
            updates=update_sql
        )

        values = [
            tuple(row.get(col) for col in columns)
            for row in rows
        ]

        execute_values(
            cursor,
            query,
            values,
            page_size=max(1, settings.CHUNK_SIZE)
        )
