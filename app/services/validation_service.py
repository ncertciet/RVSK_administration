import re
from typing import Dict, List, Any


class ValidationService:
    """
    Validates incoming payload before it reaches the mapper
    or database layer.
    """

    REQUIRED_FIELDS = [
        "udise_code",
        "state_id",
        "state_name",
        "district_id",
        "district_name",
        "school_name",
        "academic_year"
    ]

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

    INTEGER_FIELDS = [
        "state_id",
        "district_id",
        "block_id",
        "cluster_id",
        "school_category_code",
        "lowest_class_in_school",
        "highest_class_in_school",
        "total_students",
        "total_students_boys",
        "total_students_girls",
        "total_general_students",
        "total_obc_students",
        "total_sc_students",
        "total_st_students",
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
        "total_teacher_for_cwsn",
        "total_teachers_retiring",
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
        "actual_teaching_days",
        "total_smc_members"
    ]

    @classmethod
    def validate_payload(cls, records: List[Dict]):

        errors = []

        if not isinstance(records, list):
            errors.append("Payload must be a JSON array.")
            return False, errors

        if len(records) == 0:
            errors.append("Payload is empty.")
            return False, errors

        record_keys = set()

        for index, record in enumerate(records):

            row_errors = cls.validate_record(record)

            if row_errors:
                errors.append({
                    "record": index + 1,
                    "errors": row_errors
                })

            key = (
                record.get("udise_code"),
                record.get("academic_year")
            )

            if key in record_keys:
                errors.append({
                    "record": index + 1,
                    "errors": [
                        (
                            "Duplicate record found for UDISE "
                            f"{key[0]} Academic Year {key[1]}"
                        )
                    ]
                })

            record_keys.add(key)

        return len(errors) == 0, errors

    @classmethod
    def validate_record(cls, record: Dict[str, Any]):

        errors = []

        # -----------------------
        # Required Fields
        # -----------------------

        for field in cls.REQUIRED_FIELDS:

            if field not in record:
                errors.append(f"{field} is missing")
                continue

            if record[field] in ["", None]:
                errors.append(f"{field} cannot be empty")

        # -----------------------
        # Integer Validation
        # -----------------------

        for field in cls.INTEGER_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            try:
                int(value)
            except Exception:
                errors.append(f"{field} must be integer")

        # -----------------------
        # Boolean Validation
        # -----------------------

        valid_boolean = [
            True,
            False,
            "Yes",
            "No",
            "Y",
            "N",
            "yes",
            "no",
            "true",
            "false",
            "1",
            "0",
            1,
            0
        ]

        for field in cls.BOOLEAN_FIELDS:

            if field not in record:
                continue

            value = record[field]

            if value is None:
                continue

            if value not in valid_boolean:
                errors.append(
                    f"{field} must be Yes/No or True/False"
                )

        # -----------------------
        # Academic Year
        # -----------------------

        year = record.get("academic_year")

        if year:

            match = re.fullmatch(r"(\d{4})-(\d{2})", str(year))

            if not match:
                errors.append(
                    "academic_year format should be like 2024-25"
                )
            else:
                start_year = int(match.group(1))
                end_year = int(match.group(2))

                if end_year != (start_year + 1) % 100:
                    errors.append(
                        "academic_year end year should follow start year"
                    )

        # -----------------------
        # Latitude Longitude
        # -----------------------

        lat = record.get("latitude")
        lon = record.get("longitude")

        try:

            if lat is not None:

                lat = float(lat)

                if lat < -90 or lat > 90:
                    errors.append("latitude invalid")

        except Exception:
            errors.append("latitude invalid")

        try:

            if lon is not None:

                lon = float(lon)

                if lon < -180 or lon > 180:
                    errors.append("longitude invalid")

        except Exception:
            errors.append("longitude invalid")

        # -----------------------
        # Student Count Validation
        # -----------------------

        total = record.get("total_students")

        boys = record.get("total_students_boys")

        girls = record.get("total_students_girls")

        try:

            if total is not None and boys is not None and girls is not None:

                if int(total) != int(boys) + int(girls):

                    errors.append(
                        "total_students != boys + girls"
                    )

        except Exception:
            pass

        # -----------------------
        # Teacher Count Validation
        # -----------------------

        teachers = record.get("total_teachers")

        male = record.get("total_teachers_male")

        female = record.get("total_teachers_female")

        transgender = record.get("total_teachers_transgender")

        try:

            if (
                teachers is not None
                and male is not None
                and female is not None
                and transgender is not None
            ):

                if int(teachers) != (
                    int(male)
                    + int(female)
                    + int(transgender)
                ):

                    errors.append(
                        "total_teachers mismatch"
                    )

        except Exception:
            pass

        return errors
