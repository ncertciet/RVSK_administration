"""
Central table configuration.

This file tells the ingestion engine:

1. Which tables exist.
2. Which columns belong to each table.
3. What is the conflict key (Primary Key / Unique Key).
"""

TABLES = {

    # ==========================================================
    # MASTER SCHOOL
    # ==========================================================

    "master_schools_location": {

        "primary_key": [
            "udise_code"
        ],

        "columns": [

            "udise_code",
            "state_id",
            "state_name",
            "district_id",
            "district_name",
            "block_id",
            "block_name",
            "cluster_id",
            "cluster_name",
            "school_location_type",
            "school_name",
            "latitude",
            "longitude",
            "is_active",
            "school_management_type",
            "type_of_school",
            "school_category_code",
            "school_classification",
            "minority_managed",
            "lowest_class_in_school",
            "highest_class_in_school",
            "year_of_establishment"

        ]

    },

    # ==========================================================
    # ENROLLMENT
    # ==========================================================

    "school_enrollment_statistics": {

        "primary_key": [
            "udise_code",
            "academic_year"
        ],

        "columns": [

            "udise_code",
            "academic_year",
            "total_students",
            "total_students_boys",
            "total_students_girls",
            "total_general_students",
            "total_obc_students",
            "total_sc_students",
            "total_st_students"

        ]

    },

    # ==========================================================
    # TEACHERS
    # ==========================================================

    "school_teacher_statistics": {

        "primary_key": [
            "udise_code",
            "academic_year"
        ],

        "columns": [

            "udise_code",
            "academic_year",
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
            "total_teacher_for_cwsn"

        ]

    },

    # ==========================================================
    # INFRASTRUCTURE
    # ==========================================================

    "school_infrastructure": {

        "primary_key": [
            "udise_code",
            "academic_year"
        ],

        "columns": [

            "udise_code",
            "academic_year",
            "internet_availability",
            "electricity_availability",
            "smart_classrooms_availability",
            "toilet_availability",
            "total_boys_toilet",
            "total_girls_toilet",
            "total_cwsn_toilets",
            "functional_boys_toilet",
            "functional_girls_toilet",
            "functional_cwsn_toilets",
            "drinking_water_availability",
            "boundary_wall_type",
            "fire_extinguisher_available",
            "is_computer_room",
            "is_ict_lab",
            "total_laptops",
            "total_functional_desktops",
            "total_functional_laptops",
            "total_functional_tablets",
            "total_functional_digital_boards",
            "total_functional_projectors"

        ]

    },

    # ==========================================================
    # BENEFITS
    # ==========================================================

    "school_benefit_distribution": {

        "primary_key": [
            "udise_code",
            "academic_year"
        ],

        "columns": [

            "udise_code",
            "academic_year",
            "free_uniform",
            "free_textbook_primary",
            "free_textbook_upper_primary",
            "month_name_for_free_textbook_distribution",
            "month_name_for_free_uniform_distribution_primary",
            "month_name_for_free_uniform_distribution_upper_primary"

        ]

    },

    # ==========================================================
    # SCHOOL MANAGEMENT COMMITTEE
    # ==========================================================

    "school_smc_details": {

        "primary_key": [
            "udise_code",
            "academic_year"
        ],

        "columns": [

            "udise_code",
            "academic_year",
            "smc_formation_date",
            "smc_status",
            "total_smc_members",
            "actual_teaching_days"

        ]

    }

}