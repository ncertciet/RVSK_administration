import re
from datetime import datetime
from typing import Dict, List, Any


class ValidationService:
    """
    Validates incoming Administration API payload.

    Payload format:

    [
        {
            "academic_year": "2026-27",
            "school_profile": {
                "udise_code": "17010100101",
                "state_id": 1,
                "state_name": "Meghalaya",
                ...
            },
            "student_enrolment": {...},
            "school_infrastructure": {...},
            "school_benefits": {...},
            "school_smc": {...},
            "school_teacher_statistics": {...}
        }
    ]

    The master_schools_location fields are mandatory and are validated
    from the nested school_profile section.

    Validation is performed BEFORE data reaches:
        Validation
            ↓
        Table Mapper
            ↓
        Bulk UPSERT
            ↓
        PostgreSQL
    """

    # ==========================================================
    # REQUIRED SCHOOL PROFILE FIELDS
    # ==========================================================

    REQUIRED_FIELDS = [

        # -------------------------
        # School identification
        # -------------------------

        "udise_code",

        # -------------------------
        # Location / Geography
        # -------------------------

        "state_id",
        "state_name",

        "district_id",
        "district_name",

        "block_id",
        "block_name",

        "cluster_id",
        "cluster_name",

        # -------------------------
        # School profile
        # -------------------------

        "school_location_type",
        "school_name",

        "latitude",
        "longitude",

        "is_active",

        "school_management_type",
        "type_of_school",
        "school_category_code",
        "minority_managed",

        "lowest_class_in_school",
        "highest_class_in_school",

        "year_of_establishment",
        "school_address",
        "pin_code",
        "school_management_code",
        "classification_of_school",
        "is_pm_shri_school",
        "is_minority_managed_school",
        "medium_of_instruction_1",
        "medium_of_instruction_2",
        "medium_of_instruction_3",
        "medium_of_instruction_4",
        "is_shift_school",
        "residential_school_status",

        # -------------------------
        # Academic year
        # -------------------------

        "academic_year"
    ]

    # ==========================================================
    # VARCHAR / STRING FIELDS
    #
    # These MUST arrive as JSON strings.
    # ==========================================================

    STRING_FIELDS = [

        "udise_code",
        "state_name",

        "block_id",
        "cluster_id",

        "district_name",
        "block_name",
        "cluster_name",
        "school_name",
        "minority_managed"
    ]

    # ==========================================================
    # INTEGER FIELDS
    #
    # These MUST arrive as JSON integers.
    # ==========================================================

    INTEGER_FIELDS = [

        "state_id",
        "district_id",
        "school_management_type",
        "school_category_code",

        "lowest_class_in_school",
        "highest_class_in_school",

        "school_management_code",
        "classification_of_school",
        "is_pm_shri_school",
        "is_minority_managed_school",
        "medium_of_instruction_1",
        "medium_of_instruction_2",
        "medium_of_instruction_3",
        "medium_of_instruction_4",
        "is_shift_school",
        "residential_school_status",

        # ------------------------------------------------------
        # Students
        # ------------------------------------------------------

        "total_students",
        "total_cwsn_students",

        "total_students_boys",
        "total_students_girls",
        "total_students_transgender",

        "total_general_students",
        "total_obc_students",
        "total_sc_students",
        "total_st_students",

        # ------------------------------------------------------
        # Pre-primary
        # ------------------------------------------------------

        "pp1_b",
        "pp1_g",
        "pp1_t",

        "pp2_b",
        "pp2_g",
        "pp2_t",

        "pp3_b",
        "pp3_g",
        "pp3_t",

        # ------------------------------------------------------
        # Grades 1-12
        # ------------------------------------------------------

        "1_b",
        "1_g",
        "1_t",

        "2_b",
        "2_g",
        "2_t",

        "3_b",
        "3_g",
        "3_t",

        "4_b",
        "4_g",
        "4_t",

        "5_b",
        "5_g",
        "5_t",

        "6_b",
        "6_g",
        "6_t",

        "7_b",
        "7_g",
        "7_t",

        "8_b",
        "8_g",
        "8_t",

        "9_b",
        "9_g",
        "9_t",

        "10_b",
        "10_g",
        "10_t",

        "11_b",
        "11_g",
        "11_t",

        "12_b",
        "12_g",
        "12_t",

        # ------------------------------------------------------
        # Infrastructure
        # ------------------------------------------------------

        "total_boys_toilet",
        "total_girls_toilet",
        "total_cwsn_toilets",

        "functional_boys_toilet",
        "functional_girls_toilet",
        "functional_cwsn_toilets",

        "total_laptops",
        "total_functional_desktops",
        "total_functional_laptops",
        "total_functional_tablets",
        "total_functional_digital_boards",
        "total_functional_projectors",

        "total_mobile",

        # ------------------------------------------------------
        # SMC
        # ------------------------------------------------------

        "smc_status",
        "total_smc_members",

        # ------------------------------------------------------
        # Teachers
        # ------------------------------------------------------

        "actual_teaching_days",

        "total_teachers",
        "total_teachers_male",
        "total_teachers_female",
        "total_teachers_transgender",

        "total_teacher_prt",
        "total_teacher_tgt",
        "total_teacher_pgt",

        "total_teachers_pg",
        "total_teachers_ug",
        "total_teachers_bed",

        "total_regular_teachers",
        "total_contract_teachers",

        "total_teachers_joined",
        "total_teachers_retiring",

        "total_teacher_for_cwsn",

        "total_non_teaching_staff"
    ]

    # ==========================================================
    # FLOAT FIELDS
    # ==========================================================

    FLOAT_FIELDS = [
        "latitude",
        "longitude"
    ]

    # ==========================================================
    # BOOLEAN FIELDS
    #
    # These MUST arrive as actual JSON true/false.
    # ==========================================================

    BOOLEAN_FIELDS = [

        "is_active",

        "internet_availability",
        "electricity_availability",
        "smart_classrooms_availability",
        "toilet_availability",
        "drinking_water_availability",

        "fire_extinguisher_available",
        "is_computer_room",
        "is_ict_lab",

        "free_uniform",
        "free_textbook_primary",
        "free_textbook_upper_primary"
    ]

    # ==========================================================
    # DATE FIELDS
    # ==========================================================

    DATE_FIELDS = [
        "smc_formation_date"
    ]

    # ==========================================================
    # MONTH / TEXT FIELDS
    # ==========================================================

    TEXT_FIELDS = [
        "month_name_for_free_textbook_distribution",
        "month_name_for_free_uniform_distribution_primary",
        "month_name_for_free_uniform_distribution_upper_primary"
    ]

    # ==========================================================
    # NESTED PAYLOAD NORMALIZATION
    # ==========================================================

    @classmethod
    def normalize_record(
        cls,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Flatten the nested API payload for validation only.

        The original nested record is NEVER modified. This allows the
        TableMapper to continue receiving the original nested payload.
        """

        if not isinstance(record, dict):
            return {}

        normalized: Dict[str, Any] = {}

        sections = {
            "school_profile",
            "student_enrolment",
            "school_infrastructure",
            "school_benefits",
            "school_smc",
            "school_teacher_statistics",
        }

        # Keep top-level fields such as academic_year.
        for key, value in record.items():
            if key not in sections:
                normalized[key] = value

        # Merge nested sections.
        for section in sections:
            section_data = record.get(section)

            if isinstance(section_data, dict):
                normalized.update(section_data)

        return normalized

    # ==========================================================
    # MAIN PAYLOAD VALIDATION
    # ==========================================================

    @classmethod
    def validate_payload(cls, records: List[Dict[str, Any]]):
        """
        Validate the complete batch and separate valid/invalid records.

        This method intentionally does NOT fail the complete batch when a
        single record is invalid. Every record is validated independently.

        Returns:
            (valid_records, failed_records)

        Example:
            100,000 received
              99,500 valid -> sent to mapper / bulk UPSERT
                 500 invalid -> returned in failed_records
        """

        valid_records: List[Dict[str, Any]] = []
        failed_records: List[Dict[str, Any]] = []

        # ------------------------------------------------------
        # Payload must be a list
        # ------------------------------------------------------
        if not isinstance(records, list):
            failed_records.append({
                "record": None,
                "udise_code": None,
                "errors": ["Payload must be a JSON array."]
            })
            return valid_records, failed_records

        # ------------------------------------------------------
        # Empty payload
        # ------------------------------------------------------
        if not records:
            failed_records.append({
                "record": None,
                "udise_code": None,
                "errors": ["Payload is empty."]
            })
            return valid_records, failed_records

        # ------------------------------------------------------
        # Duplicate detection inside the current request.
        # Same UDISE + academic year is treated as a duplicate.
        # Database update-vs-insert behavior is handled by the ingestion
        # layer using the table primary key / UPSERT constraint.
        # ------------------------------------------------------
        record_keys = set()

        # ------------------------------------------------------
        # Validate EVERY record independently.
        # ------------------------------------------------------
        for index, record in enumerate(records):

            if not isinstance(record, dict):
                failed_records.append({
                    "record": index + 1,
                    "udise_code": None,
                    "errors": ["Each record must be a JSON object."]
                })
                continue

            normalized_record = cls.normalize_record(record)

            row_errors = cls.validate_record(normalized_record)

            key = (
                normalized_record.get("udise_code"),
                normalized_record.get("academic_year")
            )

            # Only perform duplicate detection when the key contains values.
            # This avoids reporting all records with missing required fields
            # as duplicates of one another.
            if key[0] is not None and key[1] is not None:
                if key in record_keys:
                    row_errors.append(
                        "Duplicate record found for "
                        f"UDISE {normalized_record.get('udise_code')} "
                        f"Academic Year {normalized_record.get('academic_year')}"
                    )
                else:
                    record_keys.add(key)

            # --------------------------------------------------
            # Valid record -> continue to mapper / ingestion.
            # --------------------------------------------------
            if not row_errors:
                valid_records.append(record)
                continue

            # --------------------------------------------------
            # Invalid record -> collect it, but DO NOT stop batch.
            # --------------------------------------------------
            failed_records.append({
                "record": index + 1,
                "udise_code": normalized_record.get("udise_code"),
                "errors": row_errors
            })

        return valid_records, failed_records

    # ==========================================================
    # SINGLE RECORD VALIDATION
    # ==========================================================

    @classmethod
    def validate_record(
        cls,
        record: Dict[str, Any]
    ) -> List[str]:

        # Support direct validation of either nested or normalized records.
        record = cls.normalize_record(record)

        errors = []

        # ======================================================
        # REQUIRED FIELD VALIDATION
        # ======================================================

        for field in cls.REQUIRED_FIELDS:

            if field not in record:

                errors.append(
                    f"{field} is missing"
                )

                continue

            value = record[field]

            if value is None:

                errors.append(
                    f"{field} cannot be null"
                )

            elif isinstance(value, str) and value.strip() == "":

                errors.append(
                    f"{field} cannot be empty"
                )

        # ======================================================
        # STRING / VARCHAR VALIDATION
        # ======================================================

        for field in cls.STRING_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if not isinstance(value, str):

                errors.append(
                    f"{field} must be a string/VARCHAR value"
                )

        # ======================================================
        # INTEGER VALIDATION
        #
        # IMPORTANT:
        # bool is subclass of int in Python.
        # Therefore bool is explicitly rejected.
        # ======================================================

        for field in cls.INTEGER_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if isinstance(value, bool):

                errors.append(
                    f"{field} must be an integer"
                )

                continue

            if not isinstance(value, int):

                errors.append(
                    f"{field} must be an integer"
                )

        # ======================================================
        # MASTER-SCHOOL CODE FIELD VALIDATION
        # ======================================================
        #
        # These columns are VARCHAR in the target schema, but State ERP
        # systems may send numeric JSON values. Accept both string and
        # integer representations and reject other types.
        # ======================================================

        flexible_code_fields = [
            "block_id",
            "cluster_id",
            "school_location_type",
            "type_of_school",
            "year_of_establishment",
        ]

        for field in flexible_code_fields:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if isinstance(value, bool) or not isinstance(value, (str, int)):
                errors.append(
                    f"{field} must be a string or integer value"
                )

        # ======================================================
        # FLOAT VALIDATION
        # ======================================================

        for field in cls.FLOAT_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if isinstance(value, bool):

                errors.append(
                    f"{field} must be a number"
                )

                continue

            if not isinstance(value, (int, float)):

                errors.append(
                    f"{field} must be a number"
                )

        # ======================================================
        # BOOLEAN VALIDATION
        #
        # Only true / false accepted.
        #
        # "Yes"
        # "No"
        # "1"
        # "0"
        #
        # are rejected.
        # ======================================================

        for field in cls.BOOLEAN_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            # Accept native JSON booleans and 0/1 integer flags.
            # The mapper/database layer should normalize 0/1 to boolean
            # before writing to PostgreSQL BOOLEAN columns.
            if isinstance(value, bool):
                continue

            if isinstance(value, int) and value in (0, 1):
                continue

            errors.append(
                f"{field} must be boolean true/false or 0/1"
            )

        # ======================================================
        # DATE VALIDATION
        # ======================================================

        for field in cls.DATE_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if not isinstance(value, str):

                errors.append(
                    f"{field} must be in YYYY-MM-DD format"
                )

                continue

            try:

                datetime.strptime(
                    value,
                    "%Y-%m-%d"
                )

            except ValueError:

                errors.append(
                    f"{field} must be in YYYY-MM-DD format"
                )

        # ======================================================
        # ACADEMIC YEAR VALIDATION
        # ======================================================

        academic_year = record.get("academic_year")

        if academic_year is not None:

            if not isinstance(academic_year, str):

                errors.append(
                    "academic_year must be a string"
                )

            else:

                match = re.fullmatch(
                    r"(\d{4})-(\d{2})",
                    academic_year
                )

                if not match:

                    errors.append(
                        "academic_year format should be like 2026-27"
                    )

                else:

                    start_year = int(match.group(1))
                    end_year = int(match.group(2))

                    if end_year != (start_year + 1) % 100:

                        errors.append(
                            "academic_year end year should "
                            "follow start year"
                        )

        # ======================================================
        # UDISE CODE VALIDATION
        # ======================================================

        udise_code = record.get("udise_code")

        if udise_code is not None:

            if not isinstance(udise_code, str):

                errors.append(
                    "udise_code must be a string/VARCHAR"
                )

            else:

                if not re.fullmatch(
                    r"[A-Za-z0-9]{11}",
                    udise_code
                ):

                    errors.append(
                        "udise_code must contain exactly "
                        "11 alphanumeric characters"
                    )

        # ======================================================
        # LATITUDE VALIDATION
        # ======================================================

        latitude = record.get("latitude")

        if latitude is not None:

            try:

                latitude = float(latitude)

                if latitude < -90 or latitude > 90:

                    errors.append(
                        "latitude must be between -90 and 90"
                    )

            except Exception:

                errors.append(
                    "latitude must be a valid number"
                )

        # ======================================================
        # LONGITUDE VALIDATION
        # ======================================================

        longitude = record.get("longitude")

        if longitude is not None:

            try:

                longitude = float(longitude)

                if longitude < -180 or longitude > 180:

                    errors.append(
                        "longitude must be between -180 and 180"
                    )

            except Exception:

                errors.append(
                    "longitude must be a valid number"
                )

        # ======================================================
        # SCHOOL CLASS VALIDATION
        # ======================================================

        lowest_class = record.get(
            "lowest_class_in_school"
        )

        highest_class = record.get(
            "highest_class_in_school"
        )

        if (
            isinstance(lowest_class, int)
            and not isinstance(lowest_class, bool)
            and isinstance(highest_class, int)
            and not isinstance(highest_class, bool)
        ):

            if lowest_class > highest_class:

                errors.append(
                    "lowest_class_in_school cannot be "
                    "greater than highest_class_in_school"
                )

        # ======================================================
        # STUDENT COUNT VALIDATION
        # ======================================================

        total = record.get("total_students")
        boys = record.get("total_students_boys")
        girls = record.get("total_students_girls")
        transgender = record.get("total_students_transgender")

        if all(
            isinstance(x, int) and not isinstance(x, bool)
            for x in [total, boys, girls, transgender]
        ):

            if total != boys + girls + transgender:

                errors.append(
                    "total_students must equal "
                    "total_students_boys + "
                    "total_students_girls + "
                    "total_students_transgender"
                )

        # ======================================================
        # STUDENT SOCIAL CATEGORY VALIDATION
        # ======================================================

        category_fields = [
            "total_general_students",
            "total_obc_students",
            "total_sc_students",
            "total_st_students"
        ]

        category_values = [
            record.get(field)
            for field in category_fields
        ]

        if all(
            isinstance(x, int) and not isinstance(x, bool)
            for x in category_values
        ):

            if sum(category_values) != total:

                errors.append(
                    "total_general_students + "
                    "total_obc_students + "
                    "total_sc_students + "
                    "total_st_students "
                    "must equal total_students"
                )

        # ======================================================
        # TEACHER COUNT VALIDATION
        # ======================================================

        teachers = record.get("total_teachers")
        male = record.get("total_teachers_male")
        female = record.get("total_teachers_female")
        transgender = record.get(
            "total_teachers_transgender"
        )

        if all(
            isinstance(x, int) and not isinstance(x, bool)
            for x in [
                teachers,
                male,
                female,
                transgender
            ]
        ):

            if teachers != male + female + transgender:

                errors.append(
                    "total_teachers must equal "
                    "total_teachers_male + "
                    "total_teachers_female + "
                    "total_teachers_transgender"
                )

        # ======================================================
        # TEACHER TYPE VALIDATION
        # ======================================================

        regular = record.get(
            "total_regular_teachers"
        )

        contract = record.get(
            "total_contract_teachers"
        )

        if (
            isinstance(teachers, int)
            and not isinstance(teachers, bool)
            and isinstance(regular, int)
            and not isinstance(regular, bool)
            and isinstance(contract, int)
            and not isinstance(contract, bool)
        ):

            if regular + contract > teachers:

                errors.append(
                    "total_regular_teachers + "
                    "total_contract_teachers "
                    "cannot be greater than total_teachers"
                )

        # ======================================================
        # RETURN ERRORS
        # ======================================================

        return errors