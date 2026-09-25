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
        API Payload
            ↓
        Validation
            ├── Valid   → TableMapper → Bulk UPSERT
            └── Invalid → failed_records (handled by API/ValidationService)
                                      ↓
                              PostgreSQL

    UPSERT business rule:
        Yearly tables:
            same UDISE + same Academic Year → UPDATE
            same UDISE + different Academic Year → INSERT

        Master school table:
            same UDISE → UPDATE
            new UDISE → INSERT

    IMPORTANT:
        The database primary key / unique constraint defined in TABLES is the
        conflict key. PostgreSQL ON CONFLICT performs the INSERT-vs-UPDATE
        decision atomically; we do NOT perform a SELECT-before-INSERT.
    """

    def __init__(self):
        self.mapper = TableMapper()

    def ingest(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Ingest only records that have already passed ValidationService.

        Invalid records must never reach this method.

        Returns:
            {
                "master_schools_location": number_of_rows_processed,
                "school_enrollment_statistics": number_of_rows_processed,
                ...
            }
        """
        conn = None
        cur = None
        summary: Dict[str, int] = {}

        try:
            conn = get_connection()
            cur = conn.cursor()

            for record_chunk in self._chunks(records):
                # ----------------------------------------------------------
                # TABLE MAPPER
                # ----------------------------------------------------------
                mapped = self.mapper.split_records(record_chunk)

                # mapped example:
                # {
                #     "master_schools_location": [...],
                #     "school_enrollment_statistics": [...],
                #     ...
                # }
                for table_name, table_records in mapped.items():

                    if not table_records:
                        continue

                    # ------------------------------------------------------
                    # BULK UPSERT
                    #
                    # PostgreSQL decides:
                    #
                    #   conflict on PK/unique key
                    #       -> UPDATE
                    #
                    #   no conflict
                    #       -> INSERT
                    # ------------------------------------------------------
                    self._bulk_upsert(
                        cur,
                        table_name,
                        table_records
                    )

                    summary[table_name] = (
                        summary.get(table_name, 0)
                        + len(table_records)
                    )

            # Commit the complete batch as one transaction.
            conn.commit()

            logger.info(
                "Transaction committed successfully. "
                "Records processed: %s",
                len(records)
            )

            return summary

        except Exception as ex:
            if conn is not None:
                conn.rollback()

            logger.exception(
                "Ingestion transaction rolled back: %s",
                ex
            )
            raise

        finally:
            if cur is not None:
                cur.close()

            if conn is not None:
                release_connection(conn)

    def _chunks(self, records: List[Dict[str, Any]]):
        """
        Split a large payload into configurable chunks.
        """
        chunk_size = max(1, settings.CHUNK_SIZE)

        for index in range(0, len(records), chunk_size):
            yield records[index:index + chunk_size]

    def _bulk_upsert(
        self,
        cursor,
        table_name: str,
        rows: List[Dict[str, Any]]
    ):
        """
        Bulk UPSERT into one administration table.

        Conflict behavior comes directly from TABLES[table_name]["primary_key"].

        Expected configuration:

        master_schools_location:
            primary_key = ["udise_code"]

        school_enrollment_statistics:
            primary_key = ["udise_code", "academic_year"]

        school_infrastructure:
            primary_key = ["udise_code", "academic_year"]

        school_benefit_distribution:
            primary_key = ["udise_code", "academic_year"]

        school_smc_details:
            primary_key = ["udise_code", "academic_year"]

        school_teacher_statistics:
            primary_key = ["udise_code", "academic_year"]

        Therefore:

        Master:
            same UDISE → UPDATE
            new UDISE  → INSERT

        Yearly tables:
            same UDISE + same academic_year → UPDATE
            same UDISE + different academic_year → INSERT
        """

        if not rows:
            return

        if table_name not in TABLES:
            raise ValueError(
                f"Table '{table_name}' is not configured in TABLES."
            )

        config = TABLES[table_name]

        columns = config["columns"]
        pk = config["primary_key"]

        # --------------------------------------------------------------
        # Normalize primary key configuration.
        # --------------------------------------------------------------
        if isinstance(pk, str):
            pk = [pk]

        if not pk:
            raise ValueError(
                f"Table '{table_name}' must define a primary_key."
            )

        # Every conflict column must exist in the configured columns.
        missing_pk_columns = [
            column for column in pk
            if column not in columns
        ]

        if missing_pk_columns:
            raise ValueError(
                f"Table '{table_name}' primary key columns "
                f"{missing_pk_columns} are not present in TABLES columns."
            )

        # --------------------------------------------------------------
        # Prevent audit columns from being overwritten by the payload.
        #
        # created_date / updated_date should be DB-managed.
        # They should therefore NOT normally be present in table_schema.py.
        # --------------------------------------------------------------
        payload_columns = [
            column
            for column in columns
            if column not in ("created_date", "updated_date")
        ]

        if not payload_columns:
            raise ValueError(
                f"No payload columns configured for '{table_name}'."
            )

        # --------------------------------------------------------------
        # Columns to update when a conflict occurs.
        #
        # Primary-key columns are never updated.
        # --------------------------------------------------------------
        update_columns = [
            column
            for column in payload_columns
            if column not in pk
        ]

        # --------------------------------------------------------------
        # Build UPDATE clause.
        # --------------------------------------------------------------
        if update_columns:
            update_sql = sql.SQL(", ").join(
                sql.SQL("{column} = EXCLUDED.{column}").format(
                    column=sql.Identifier(column)
                )
                for column in update_columns
            )

            conflict_action = sql.SQL(
                "DO UPDATE SET {updates}"
            ).format(
                updates=update_sql
            )
        else:
            # Safety fallback if a table only contains its primary key.
            conflict_action = sql.SQL("DO NOTHING")

        # --------------------------------------------------------------
        # Build INSERT ... ON CONFLICT ... DO UPDATE.
        #
        # PostgreSQL atomically determines whether the conflict key
        # already exists.
        # --------------------------------------------------------------
        query = sql.SQL("""
            INSERT INTO {table}
                ({columns})
            VALUES %s
            ON CONFLICT ({conflict_columns})
            {conflict_action}
        """).format(
            table=sql.Identifier("administration", table_name),

            columns=sql.SQL(", ").join(
                sql.Identifier(column)
                for column in payload_columns
            ),

            conflict_columns=sql.SQL(", ").join(
                sql.Identifier(column)
                for column in pk
            ),

            conflict_action=conflict_action
        )

        # --------------------------------------------------------------
        # Build VALUES in exactly the same order as payload_columns.
        # --------------------------------------------------------------
        values = [
            tuple(row.get(column) for column in payload_columns)
            for row in rows
        ]

        # --------------------------------------------------------------
        # Execute bulk UPSERT.
        # --------------------------------------------------------------
        execute_values(
            cursor,
            query,
            values,
            page_size=max(1, settings.CHUNK_SIZE)
        )

        logger.info(
            "Bulk UPSERT completed: table=%s rows=%s conflict_key=%s",
            table_name,
            len(rows),
            pk
        )
