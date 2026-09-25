from copy import deepcopy
from typing import Any, Dict, List

from app.config.table_schema import TABLES


class TableMapper:
    """
    Converts the nested Administration payload into
    table-wise records.

    Payload structure:

    {
        "academic_year": "2026-27",
        "school_profile": {...},
        "student_enrolment": {...},
        "school_infrastructure": {...},
        "school_benefits": {...},
        "school_smc": {...},
        "school_teacher_statistics": {...}
    }

    Output:

    {
        "master_schools_location": [...],
        "school_enrollment_statistics": [...],
        "school_infrastructure": [...],
        ...
    }
    """

    # ============================================================
    # PAYLOAD SECTIONS
    # ============================================================

    SECTIONS = [
        "school_profile",
        "student_enrolment",
        "school_infrastructure",
        "school_benefits",
        "school_smc",
        "school_teacher_statistics",
    ]

    # ============================================================
    # DATABASE BOOLEAN COLUMNS
    # ============================================================
    #
    # These are the columns that are actually BOOLEAN in the
    # PostgreSQL administration schema.
    #
    # Accepted input:
    #
    #   true / false
    #   "true" / "false"
    #   yes / no
    #   "yes" / "no"
    #   1 / 0
    #   "1" / "0"
    #   y / n
    #   t / f
    #
    # They are converted to Python:
    #
    #   True / False
    #
    # PostgreSQL then stores them as:
    #
    #   TRUE / FALSE
    #
    # IMPORTANT:
    # Do NOT add integer/code fields here merely because they
    # contain values like 0 or 1.
    # ============================================================

    BOOLEAN_FIELDS = {
        # master_schools_location
        "is_active",

        # school_benefit_distribution
        "free_uniform",
        "free_textbook_primary",
        "free_textbook_upper_primary",

        # school_infrastructure
        "internet_availability",
        "electricity_availability",
        "smart_classrooms_availability",
        "toilet_availability",
        "drinking_water_availability",
        "fire_extinguisher_available",
        "is_computer_room",
        "is_ict_lab",
    }

    # ============================================================
    # PAYLOAD FIELD ALIASES
    # ============================================================
    #
    # Backward compatibility for older TABLES definitions.
    #
    # Example:
    #
    # Old database/config column:
    #     pp1_b
    #
    # New payload field:
    #     pp1_boys
    #
    # If table_schema.py has already been changed to the full
    # names, these aliases simply won't be used.
    # ============================================================

    FIELD_ALIASES = {

        # --------------------------------------------------------
        # PP1
        # --------------------------------------------------------

        "pp1_b": "pp1_boys",
        "pp1_g": "pp1_girls",
        "pp1_t": "pp1_transgender",

        # --------------------------------------------------------
        # PP2
        # --------------------------------------------------------

        "pp2_b": "pp2_boys",
        "pp2_g": "pp2_girls",
        "pp2_t": "pp2_transgender",

        # --------------------------------------------------------
        # PP3
        # --------------------------------------------------------

        "pp3_b": "pp3_boys",
        "pp3_g": "pp3_girls",
        "pp3_t": "pp3_transgender",

        # --------------------------------------------------------
        # Grade 1
        # --------------------------------------------------------

        "grade1_b": "grade1_boys",
        "grade1_g": "grade1_girls",
        "grade1_t": "grade1_transgender",

        # --------------------------------------------------------
        # Grade 2
        # --------------------------------------------------------

        "grade2_b": "grade2_boys",
        "grade2_g": "grade2_girls",
        "grade2_t": "grade2_transgender",

        # --------------------------------------------------------
        # Grade 3
        # --------------------------------------------------------

        "grade3_b": "grade3_boys",
        "grade3_g": "grade3_girls",
        "grade3_t": "grade3_transgender",

        # --------------------------------------------------------
        # Grade 4
        # --------------------------------------------------------

        "grade4_b": "grade4_boys",
        "grade4_g": "grade4_girls",
        "grade4_t": "grade4_transgender",

        # --------------------------------------------------------
        # Grade 5
        # --------------------------------------------------------

        "grade5_b": "grade5_boys",
        "grade5_g": "grade5_girls",
        "grade5_t": "grade5_transgender",

        # --------------------------------------------------------
        # Grade 6
        # --------------------------------------------------------

        "grade6_b": "grade6_boys",
        "grade6_g": "grade6_girls",
        "grade6_t": "grade6_transgender",

        # --------------------------------------------------------
        # Grade 7
        # --------------------------------------------------------

        "grade7_b": "grade7_boys",
        "grade7_g": "grade7_girls",
        "grade7_t": "grade7_transgender",

        # --------------------------------------------------------
        # Grade 8
        # --------------------------------------------------------

        "grade8_b": "grade8_boys",
        "grade8_g": "grade8_girls",
        "grade8_t": "grade8_transgender",

        # --------------------------------------------------------
        # Grade 9
        # --------------------------------------------------------

        "grade9_b": "grade9_boys",
        "grade9_g": "grade9_girls",
        "grade9_t": "grade9_transgender",

        # --------------------------------------------------------
        # Grade 10
        # --------------------------------------------------------

        "grade10_b": "grade10_boys",
        "grade10_g": "grade10_girls",
        "grade10_t": "grade10_transgender",

        # --------------------------------------------------------
        # Grade 11
        # --------------------------------------------------------

        "grade11_b": "grade11_boys",
        "grade11_g": "grade11_girls",
        "grade11_t": "grade11_transgender",

        # --------------------------------------------------------
        # Grade 12
        # --------------------------------------------------------

        "grade12_b": "grade12_boys",
        "grade12_g": "grade12_girls",
        "grade12_t": "grade12_transgender",
    }

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):
        self.tables = TABLES

    # ============================================================
    # FLATTEN NESTED PAYLOAD
    # ============================================================

    def flatten_record(
        self,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Flatten the nested payload into one dictionary.

        The original payload is NOT modified.
        """

        flattened: Dict[str, Any] = {}

        # --------------------------------------------------------
        # Academic year
        # --------------------------------------------------------

        if "academic_year" in record:
            flattened["academic_year"] = record["academic_year"]

        # --------------------------------------------------------
        # Flatten all supported sections
        # --------------------------------------------------------

        for section in self.SECTIONS:

            section_data = record.get(section)

            if not isinstance(section_data, dict):
                continue

            for field, value in section_data.items():
                flattened[field] = value

        return flattened

    # ============================================================
    # BOOLEAN NORMALIZATION
    # ============================================================

    def _normalize_boolean(self, value: Any) -> Any:
        """
        Convert flexible state-level boolean representations
        into Python True / False / None.

        Supported:

            True / False
            1 / 0
            "1" / "0"
            "true" / "false"
            "yes" / "no"
            "y" / "n"
            "t" / "f"

        Empty string becomes None.

        Invalid values raise ValueError instead of silently
        guessing.
        """

        if value is None:
            return None

        # --------------------------------------------------------
        # Python boolean
        # --------------------------------------------------------

        if isinstance(value, bool):
            return value

        # --------------------------------------------------------
        # Integer 0 / 1
        # --------------------------------------------------------

        if isinstance(value, int):

            if value == 1:
                return True

            if value == 0:
                return False

            raise ValueError(
                f"Invalid boolean integer value: {value}. "
                "Expected 0 or 1."
            )

        # --------------------------------------------------------
        # String values
        # --------------------------------------------------------

        if isinstance(value, str):

            normalized = value.strip().lower()

            if normalized == "":
                return None

            if normalized in {
                "true",
                "yes",
                "y",
                "1",
                "t",
            }:
                return True

            if normalized in {
                "false",
                "no",
                "n",
                "0",
                "f",
            }:
                return False

            raise ValueError(
                f"Invalid boolean value: '{value}'. "
                "Expected true/false, yes/no, or 1/0."
            )

        # --------------------------------------------------------
        # Unsupported type
        # --------------------------------------------------------

        raise ValueError(
            f"Invalid boolean value type: "
            f"{type(value).__name__}. "
            "Expected boolean, integer 0/1, or string."
        )

    # ============================================================
    # GENERAL NORMALIZATION
    # ============================================================

    def _normalize(
        self,
        column: str,
        value: Any
    ) -> Any:
        """
        Normalize a value according to its database column.

        BOOLEAN columns:
            Convert flexible input to True / False / None.

        Other columns:
            Strip strings and convert empty strings to None.
            Preserve numeric values as-is.
        """

        if value is None:
            return None

        # --------------------------------------------------------
        # BOOLEAN column
        # --------------------------------------------------------

        if column in self.BOOLEAN_FIELDS:
            return self._normalize_boolean(value)

        # --------------------------------------------------------
        # String
        # --------------------------------------------------------

        if isinstance(value, str):

            value = value.strip()

            if value == "":
                return None

            return value

        # --------------------------------------------------------
        # Numbers / dates / other values
        # --------------------------------------------------------

        return value

    # ============================================================
    # GET VALUE FOR DATABASE COLUMN
    # ============================================================

    def _get_column_value(
        self,
        column: str,
        flat_record: Dict[str, Any]
    ) -> Any:
        """
        Get the correct payload value for a database column.

        Priority:

        1. Exact column name exists in payload.
        2. Column is an old/short alias.
        3. Return None.
        """

        # --------------------------------------------------------
        # 1. Exact database column name exists
        # --------------------------------------------------------

        if column in flat_record:

            return self._normalize(
                column,
                flat_record[column]
            )

        # --------------------------------------------------------
        # 2. Database column is an old/short alias
        # --------------------------------------------------------

        payload_field = self.FIELD_ALIASES.get(column)

        if payload_field:

            return self._normalize(
                column,
                flat_record.get(payload_field)
            )

        # --------------------------------------------------------
        # 3. Nothing available
        # --------------------------------------------------------

        return None

    # ============================================================
    # SPLIT ONE RECORD
    # ============================================================

    def split_record(
        self,
        record: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Convert one nested payload record into rows for every
        configured database table.
        """

        flat_record = self.flatten_record(record)

        result: Dict[str, Dict[str, Any]] = {}

        # --------------------------------------------------------
        # Process every configured table
        # --------------------------------------------------------

        for table_name, meta in self.tables.items():

            row: Dict[str, Any] = {}

            for column in meta["columns"]:

                row[column] = deepcopy(
                    self._get_column_value(
                        column,
                        flat_record
                    )
                )

            result[table_name] = row

        return result

    # ============================================================
    # SPLIT MULTIPLE RECORDS
    # ============================================================

    def split_records(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert multiple nested payload records into
        table-wise lists.
        """

        output = {
            table_name: []
            for table_name in self.tables.keys()
        }

        for record in records:

            split = self.split_record(record)

            for table_name, row in split.items():

                output[table_name].append(row)

        return output