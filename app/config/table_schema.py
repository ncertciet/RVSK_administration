TABLES = {

    # ==========================================================
    # 1. MASTER SCHOOL LOCATION
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
        ]
    },


    # ==========================================================
    # 2. STUDENT ENROLMENT
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
            "total_cwsn_students",
            "total_students_boys",
            "total_students_girls",
            "total_students_transgender",
            "total_general_students",
            "total_obc_students",
            "total_sc_students",
            "total_st_students",

            "pp1_boys",
            "pp1_girls",
            "pp1_transgender",

            "pp2_boys",
            "pp2_girls",
            "pp2_transgender",

            "pp3_boys",
            "pp3_girls",
            "pp3_transgender",

            "grade1_boys",
            "grade1_girls",
            "grade1_transgender",

            "grade2_boys",
            "grade2_girls",
            "grade2_transgender",

            "grade3_boys",
            "grade3_girls",
            "grade3_transgender",

            "grade4_boys",
            "grade4_girls",
            "grade4_transgender",

            "grade5_boys",
            "grade5_girls",
            "grade5_transgender",

            "grade6_boys",
            "grade6_girls",
            "grade6_transgender",

            "grade7_boys",
            "grade7_girls",
            "grade7_transgender",

            "grade8_boys",
            "grade8_girls",
            "grade8_transgender",

            "grade9_boys",
            "grade9_girls",
            "grade9_transgender",

            "grade10_boys",
            "grade10_girls",
            "grade10_transgender",

            "grade11_boys",
            "grade11_girls",
            "grade11_transgender",

            "grade12_boys",
            "grade12_girls",
            "grade12_transgender",
        ]
    },


    # ==========================================================
    # 3. SCHOOL TEACHER STATISTICS
    # ==========================================================

    "school_teacher_statistics": {

        "primary_key": [
            "udise_code",
            "academic_year"
        ],

        "columns": [

            "udise_code",
            "academic_year",
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
            "total_non_regular_teachers",
            "total_teachers_joined",
            "total_teachers_retiring",
            "total_teacher_for_cwsn",
            "total_non_teaching_staff",
        ]
    },


    # ==========================================================
    # 4. SCHOOL INFRASTRUCTURE
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
            "total_functional_projectors",
            "mobile_phone_used_for_teaching",
        ]
    },


    # ==========================================================
    # 5. SCHOOL BENEFITS
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
            "month_name_for_free_uniform_distribution_upper_primary",
        ]
    },


    # ==========================================================
    # 6. SCHOOL MANAGEMENT COMMITTEE
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
            "actual_teaching_days",
        ]
    }

}