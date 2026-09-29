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
                "udise_code": "AB345678901",
                "state_id": 1,
                "state_name": "TEST",
                ...
            },
            "student_enrolment": {...},
            "school_infrastructure": {...},
            "school_benefits": {...},
            "school_smc": {...},
            "school_teacher_statistics": {...}
        }
    ]

    Validation flow:

        Incoming Payload
              ↓
        Convert all string values to UPPER CASE
              ↓
        Normalize nested record
              ↓
        Validate all records
              ↓
        valid_records
              ↓
        TableMapper
              ↓
        Bulk UPSERT
              ↓
        PostgreSQL
    """

    # ==========================================================
    # REQUIRED FIELDS
    # ==========================================================

    REQUIRED_FIELDS = [
        # School identification
        "udise_code",

        # Location
        "state_id",
        "state_name",

        "district_id",
        "district_name",

        "block_id",
        "block_name",

        "cluster_id",
        "cluster_name",

        # School profile
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

        # Academic year
        "academic_year",
    ]

    # ==========================================================
    # STRING / VARCHAR FIELDS
    # ==========================================================

    STRING_FIELDS = [
        "udise_code",
        "state_name",

        "district_id",
        "district_name",

        "block_id",
        "block_name",

        "cluster_id",
        "cluster_name",

        "school_location_type",
        "school_name",
        "type_of_school",

        "minority_managed",
        "year_of_establishment",

        "school_address",
        "pin_code",

        "boundary_wall_type",
    ]

    # ==========================================================
    # INTEGER FIELDS
    # ==========================================================

    INTEGER_FIELDS = [
        # ------------------------------------------------------
        # School profile
        # ------------------------------------------------------

        "state_id",
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
        # Student enrolment
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

        "pp1_boys",
        "pp1_girls",
        "pp1_transgender",

        "pp2_boys",
        "pp2_girls",
        "pp2_transgender",

        "pp3_boys",
        "pp3_girls",
        "pp3_transgender",

        # ------------------------------------------------------
        # Grade 1
        # ------------------------------------------------------

        "grade1_boys",
        "grade1_girls",
        "grade1_transgender",

        # ------------------------------------------------------
        # Grade 2
        # ------------------------------------------------------

        "grade2_boys",
        "grade2_girls",
        "grade2_transgender",

        # ------------------------------------------------------
        # Grade 3
        # ------------------------------------------------------

        "grade3_boys",
        "grade3_girls",
        "grade3_transgender",

        # ------------------------------------------------------
        # Grade 4
        # ------------------------------------------------------

        "grade4_boys",
        "grade4_girls",
        "grade4_transgender",

        # ------------------------------------------------------
        # Grade 5
        # ------------------------------------------------------

        "grade5_boys",
        "grade5_girls",
        "grade5_transgender",

        # ------------------------------------------------------
        # Grade 6
        # ------------------------------------------------------

        "grade6_boys",
        "grade6_girls",
        "grade6_transgender",

        # ------------------------------------------------------
        # Grade 7
        # ------------------------------------------------------

        "grade7_boys",
        "grade7_girls",
        "grade7_transgender",

        # ------------------------------------------------------
        # Grade 8
        # ------------------------------------------------------

        "grade8_boys",
        "grade8_girls",
        "grade8_transgender",

        # ------------------------------------------------------
        # Grade 9
        # ------------------------------------------------------

        "grade9_boys",
        "grade9_girls",
        "grade9_transgender",

        # ------------------------------------------------------
        # Grade 10
        # ------------------------------------------------------

        "grade10_boys",
        "grade10_girls",
        "grade10_transgender",

        # ------------------------------------------------------
        # Grade 11
        # ------------------------------------------------------

        "grade11_boys",
        "grade11_girls",
        "grade11_transgender",

        # ------------------------------------------------------
        # Grade 12
        # ------------------------------------------------------

        "grade12_boys",
        "grade12_girls",
        "grade12_transgender",

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

        "mobile_phone_used_for_teaching",

        # ------------------------------------------------------
        # SMC
        # ------------------------------------------------------

        "total_smc_members",
        "actual_teaching_days",

        # ------------------------------------------------------
        # Teachers
        # ------------------------------------------------------

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
        "total_non_regular_teachers",

        "total_teachers_joined",
        "total_teachers_retiring",

        "total_teacher_for_cwsn",

        "total_non_teaching_staff",
    ]

    # ==========================================================
    # FLOAT FIELDS
    # ==========================================================

    FLOAT_FIELDS = [
        "latitude",
        "longitude",
    ]

    # ==========================================================
    # BOOLEAN FIELDS
    #
    # PostgreSQL BOOLEAN columns.
    #
    # Accepted:
    #   true
    #   false
    #   1
    #   0
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
        "free_textbook_upper_primary",
    ]

    # ==========================================================
    # DATE FIELDS
    # ==========================================================

    DATE_FIELDS = [
        "smc_formation_date",
    ]

    # ==========================================================
    # TEXT / MONTH FIELDS
    # ==========================================================

    TEXT_FIELDS = [
        "month_name_for_free_textbook_distribution",
        "month_name_for_free_uniform_distribution_primary",
        "month_name_for_free_uniform_distribution_upper_primary",
    ]

    # ==========================================================
    # UPPERCASE STRING VALUES
    # ==========================================================

    @classmethod
    def uppercase_strings(
        cls,
        value: Any
    ) -> Any:
        """
        Recursively convert every string VALUE to UPPER CASE.

        Examples:

            "Shillong"
                -> "SHILLONG"

            "Government Upper Primary School"
                -> "GOVERNMENT UPPER PRIMARY SCHOOL"

            "yes"
                -> "YES"

            "abc34567890"
                -> "ABC34567890"

        Numbers:
            123
                -> 123

        Booleans:
            True
                -> True

        None:
            None
                -> None

        Dictionary keys are NOT changed.

        Works recursively with:

            dict
            list
            tuple
        """

        # ------------------------------------------------------
        # String
        # ------------------------------------------------------

        if isinstance(value, str):
            return value.upper()

        # ------------------------------------------------------
        # Dictionary
        # ------------------------------------------------------

        if isinstance(value, dict):

            return {
                key: cls.uppercase_strings(val)
                for key, val in value.items()
            }

        # ------------------------------------------------------
        # List
        # ------------------------------------------------------

        if isinstance(value, list):

            return [
                cls.uppercase_strings(item)
                for item in value
            ]

        # ------------------------------------------------------
        # Tuple
        # ------------------------------------------------------

        if isinstance(value, tuple):

            return tuple(
                cls.uppercase_strings(item)
                for item in value
            )

        # ------------------------------------------------------
        # Numbers / Boolean / None / Other
        # ------------------------------------------------------

        return value

    # ==========================================================
    # NESTED PAYLOAD NORMALIZATION
    # ==========================================================

    @classmethod
    def normalize_record(
        cls,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Flatten nested API payload for validation only.

        IMPORTANT:
        The original nested record is NOT modified.

        Example:

            {
                "academic_year": "2026-27",
                "school_profile": {
                    "udise_code": "AB345678901"
                }
            }

        becomes internally:

            {
                "academic_year": "2026-27",
                "udise_code": "AB345678901"
            }
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

        # ------------------------------------------------------
        # Keep top-level fields
        # ------------------------------------------------------

        for key, value in record.items():

            if key not in sections:
                normalized[key] = value

        # ------------------------------------------------------
        # Flatten nested sections
        # ------------------------------------------------------

        for section in sections:

            section_data = record.get(section)

            if isinstance(section_data, dict):
                normalized.update(section_data)

        return normalized

    # ==========================================================
    # MAIN PAYLOAD VALIDATION
    # ==========================================================

    @classmethod
    def validate_payload(
        cls,
        records: List[Dict[str, Any]]
    ):
        """
        Validate complete batch.

        Returns:

            valid_records,
            failed_records

        Every record is validated independently.

        Example:

            100000 received
              99500 valid
                500 invalid

        Result:

            valid_records   = 99500
            failed_records  = 500

        IMPORTANT:

        Valid records returned from this method are already
        converted to UPPER CASE for all string values.
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
                "errors": [
                    "Payload must be a JSON array."
                ]
            })

            return valid_records, failed_records

        # ------------------------------------------------------
        # Empty payload
        # ------------------------------------------------------

        if not records:

            failed_records.append({
                "record": None,
                "udise_code": None,
                "errors": [
                    "Payload is empty."
                ]
            })

            return valid_records, failed_records

        # ------------------------------------------------------
        # Duplicate detection
        # ------------------------------------------------------

        record_keys = set()

        # ------------------------------------------------------
        # Validate EVERY record
        # ------------------------------------------------------

        for index, record in enumerate(records):

            # --------------------------------------------------
            # Record must be an object
            # --------------------------------------------------

            if not isinstance(record, dict):

                failed_records.append({
                    "record": index + 1,
                    "udise_code": None,
                    "errors": [
                        "Each record must be a JSON object."
                    ]
                })

                continue

            # --------------------------------------------------
            # Convert ALL string values to UPPER CASE
            # --------------------------------------------------

            uppercase_record = cls.uppercase_strings(
                record
            )

            # --------------------------------------------------
            # Flatten uppercase record for validation
            # --------------------------------------------------

            normalized_record = cls.normalize_record(
                uppercase_record
            )

            # --------------------------------------------------
            # Validate record
            # --------------------------------------------------

            row_errors = cls.validate_record(
                normalized_record
            )

            # --------------------------------------------------
            # Duplicate key
            #
            # Since the record has already been uppercased,
            # UDISE values such as:
            #
            #   ab345678901
            #   AB345678901
            #
            # are treated as the same value.
            # --------------------------------------------------

            key = (
                normalized_record.get("udise_code"),
                normalized_record.get("academic_year")
            )

            if (
                key[0] is not None
                and key[1] is not None
            ):

                if key in record_keys:

                    row_errors.append(
                        "Duplicate record found for "
                        f"UDISE {normalized_record.get('udise_code')} "
                        f"Academic Year "
                        f"{normalized_record.get('academic_year')}"
                    )

                else:

                    record_keys.add(key)

            # --------------------------------------------------
            # Valid
            #
            # IMPORTANT:
            # Append uppercase_record, NOT original record.
            # This ensures the DB receives uppercase strings.
            # --------------------------------------------------

            if not row_errors:

                valid_records.append(
                    uppercase_record
                )

                continue

            # --------------------------------------------------
            # Invalid
            # --------------------------------------------------

            failed_records.append({
                "record": index + 1,
                "udise_code": normalized_record.get(
                    "udise_code"
                ),
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

        # ------------------------------------------------------
        # Support nested or already-normalized records
        # ------------------------------------------------------

        record = cls.normalize_record(record)

        errors: List[str] = []

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

            elif (
                isinstance(value, str)
                and value.strip() == ""
            ):

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
        # ======================================================

        for field in cls.INTEGER_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            # bool is a subclass of int in Python
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
        # FLOAT / NUMERIC VALIDATION
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

            if not isinstance(
                value,
                (int, float)
            ):

                errors.append(
                    f"{field} must be a number"
                )

        # ======================================================
        # BOOLEAN VALIDATION
        #
        # Accepted:
        #
        #   true
        #   false
        #   0
        #   1
        # ======================================================

        for field in cls.BOOLEAN_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if isinstance(value, bool):
                continue

            if (
                isinstance(value, int)
                and value in (0, 1)
            ):
                continue

            errors.append(
                f"{field} must be boolean "
                f"true/false or 0/1"
            )

        # ======================================================
        # SMC STATUS VALIDATION
        #
        # Database type:
        #     VARCHAR(100)
        #
        # Accepted API values:
        #
        #     1
        #     2
        #     "1"
        #     "2"
        #     "Yes"
        #     "No"
        #
        # Case-insensitive for Yes/No.
        # ======================================================

        smc_status = record.get(
            "smc_status"
        )

        if smc_status is not None:

            if isinstance(
                smc_status,
                bool
            ):

                errors.append(
                    "smc_status must be one of: "
                    "1, 2, Yes, No"
                )

            elif isinstance(
                smc_status,
                int
            ):

                if smc_status not in (1, 2):

                    errors.append(
                        "smc_status must be one of: "
                        "1, 2, Yes, No"
                    )

            elif isinstance(
                smc_status,
                str
            ):

                normalized_status = (
                    smc_status.strip().lower()
                )

                if normalized_status not in (
                    "1",
                    "2",
                    "yes",
                    "no",
                ):

                    errors.append(
                        "smc_status must be one of: "
                        "1, 2, Yes, No"
                    )

            else:

                errors.append(
                    "smc_status must be one of: "
                    "1, 2, Yes, No"
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

            if not isinstance(
                value,
                str
            ):

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

        academic_year = record.get(
            "academic_year"
        )

        if academic_year is not None:

            if not isinstance(
                academic_year,
                str
            ):

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
                        "academic_year format should be "
                        "like 2026-27"
                    )

                else:

                    start_year = int(
                        match.group(1)
                    )

                    end_year = int(
                        match.group(2)
                    )

                    if end_year != (
                        (start_year + 1) % 100
                    ):

                        errors.append(
                            "academic_year end year should "
                            "follow start year"
                        )

        # ======================================================
        # UDISE CODE VALIDATION
        # ======================================================

        udise_code = record.get(
            "udise_code"
        )

        if udise_code is not None:

            if not isinstance(
                udise_code,
                str
            ):

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

        latitude = record.get(
            "latitude"
        )

        if latitude is not None:

            if isinstance(
                latitude,
                bool
            ):

                errors.append(
                    "latitude must be a valid number"
                )

            elif not isinstance(
                latitude,
                (int, float)
            ):

                errors.append(
                    "latitude must be a valid number"
                )

            else:

                if latitude < -90 or latitude > 90:

                    errors.append(
                        "latitude must be between "
                        "-90 and 90"
                    )

        # ======================================================
        # LONGITUDE VALIDATION
        # ======================================================

        longitude = record.get(
            "longitude"
        )

        if longitude is not None:

            if isinstance(
                longitude,
                bool
            ):

                errors.append(
                    "longitude must be a valid number"
                )

            elif not isinstance(
                longitude,
                (int, float)
            ):

                errors.append(
                    "longitude must be a valid number"
                )

            else:

                if longitude < -180 or longitude > 180:

                    errors.append(
                        "longitude must be between "
                        "-180 and 180"
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
            isinstance(
                lowest_class,
                int
            )
            and not isinstance(
                lowest_class,
                bool
            )
            and isinstance(
                highest_class,
                int
            )
            and not isinstance(
                highest_class,
                bool
            )
        ):

            if lowest_class > highest_class:

                errors.append(
                    "lowest_class_in_school cannot be "
                    "greater than highest_class_in_school"
                )

        # ======================================================
        # STUDENT TOTAL VALIDATION
        # ======================================================

        total_students = record.get(
            "total_students"
        )

        boys = record.get(
            "total_students_boys"
        )

        girls = record.get(
            "total_students_girls"
        )

        transgender = record.get(
            "total_students_transgender"
        )

        if all(
            isinstance(value, int)
            and not isinstance(value, bool)
            for value in [
                total_students,
                boys,
                girls,
                transgender,
            ]
        ):

            if total_students != (
                boys
                + girls
                + transgender
            ):

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
            "total_st_students",
        ]

        category_values = [
            record.get(field)
            for field in category_fields
        ]

        if all(
            isinstance(value, int)
            and not isinstance(value, bool)
            for value in category_values
        ):

            if sum(category_values) != total_students:

                errors.append(
                    "total_general_students + "
                    "total_obc_students + "
                    "total_sc_students + "
                    "total_st_students "
                    "must equal total_students"
                )

        # ======================================================
        # TEACHER TOTAL VALIDATION
        # ======================================================

        total_teachers = record.get(
            "total_teachers"
        )

        male = record.get(
            "total_teachers_male"
        )

        female = record.get(
            "total_teachers_female"
        )

        teacher_transgender = record.get(
            "total_teachers_transgender"
        )

        if all(
            isinstance(value, int)
            and not isinstance(value, bool)
            for value in [
                total_teachers,
                male,
                female,
                teacher_transgender,
            ]
        ):

            if total_teachers != (
                male
                + female
                + teacher_transgender
            ):

                errors.append(
                    "total_teachers must equal "
                    "total_teachers_male + "
                    "total_teachers_female + "
                    "total_teachers_transgender"
                )

        # ======================================================
        # TEACHER TYPE VALIDATION
        #
        # total_regular_teachers +
        # total_non_regular_teachers
        #
        # must equal total_teachers
        # ======================================================

        regular_teachers = record.get(
            "total_regular_teachers"
        )

        non_regular_teachers = record.get(
            "total_non_regular_teachers"
        )

        if (
            isinstance(
                total_teachers,
                int
            )
            and not isinstance(
                total_teachers,
                bool
            )
            and isinstance(
                regular_teachers,
                int
            )
            and not isinstance(
                regular_teachers,
                bool
            )
            and isinstance(
                non_regular_teachers,
                int
            )
            and not isinstance(
                non_regular_teachers,
                bool
            )
        ):

            if (
                regular_teachers
                + non_regular_teachers
                != total_teachers
            ):

                errors.append(
                    "total_regular_teachers + "
                    "total_non_regular_teachers "
                    "must equal total_teachers"
                )

        # ======================================================
        # RETURN VALIDATION ERRORS
        # ======================================================

        return errors