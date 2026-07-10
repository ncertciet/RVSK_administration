CREATE UNIQUE INDEX IF NOT EXISTS ux_master_schools_location_udise_code
ON administration.master_schools_location (udise_code);

CREATE UNIQUE INDEX IF NOT EXISTS ux_school_enrollment_statistics_udise_year
ON administration.school_enrollment_statistics (udise_code, academic_year);

CREATE UNIQUE INDEX IF NOT EXISTS ux_school_teacher_statistics_udise_year
ON administration.school_teacher_statistics (udise_code, academic_year);

CREATE UNIQUE INDEX IF NOT EXISTS ux_school_infrastructure_udise_year
ON administration.school_infrastructure (udise_code, academic_year);

CREATE UNIQUE INDEX IF NOT EXISTS ux_school_benefit_distribution_udise_year
ON administration.school_benefit_distribution (udise_code, academic_year);

CREATE UNIQUE INDEX IF NOT EXISTS ux_school_smc_details_udise_year
ON administration.school_smc_details (udise_code, academic_year);

