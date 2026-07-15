# Data Dictionary — Smart Attendance Pattern Analyzer

## attendance_dataset.csv (main dataset, one row per student per subject)

| Column | Type | Description |
|---|---|---|
| Student_ID | string | Unique student identifier, e.g. STU00001 |
| Name | string | Student full name (synthetic) |
| Department | string | Department / branch of study |
| Semester | int | Current semester (1-8) |
| Gender | string | Male / Female |
| Subject | string | Subject name this row's attendance relates to |
| Total_Classes | int | Total classes held for the subject this term |
| Classes_Attended | int | Classes the student attended |
| Attendance_Percentage | float | Classes_Attended / Total_Classes * 100 |
| Previous_Attendance_Percentage | float | Attendance % in the previous semester |
| Leaves_Taken | int | Number of leaves taken during the term |
| Internal_Marks | int | Internal assessment marks (0-100) |
| Distance_KM | float | Student's distance from college in kilometers |
| Monthly_Attendance | float | Most recent month's attendance % (see monthly_attendance.csv for full series) |
| Trend | string | Hidden behavioural trend used to generate the data: improving / stable / declining |
| Risk_Label | string | Target label: Low Risk / Medium Risk / High Risk |

## monthly_attendance.csv (long format)

| Column | Type | Description |
|---|---|---|
| Student_ID | string | Unique student identifier |
| Subject | string | Subject name |
| Month | string | Month abbreviation (Jan-Jun, 6-month rolling window) |
| Attendance_Percentage | float | Attendance % for that student/subject/month |

## students_master.csv (one row per student)

| Column | Type | Description |
|---|---|---|
| Student_ID | string | Unique student identifier |
| Name | string | Student full name |
| Department | string | Department / branch |
| Semester | int | Current semester |
| Gender | string | Male / Female |
| Distance_KM | float | Distance from college |
| Overall_Attendance_Percentage | float | Average attendance % across all enrolled subjects |
| Trend | string | improving / stable / declining |
| Num_Subjects | int | Number of subjects the student is enrolled in |

## Generation Notes

- Data is fully synthetic, generated with NumPy + Faker using seeded RNG for reproducibility.
- Attendance is modeled with a per-student "diligence" factor (Beta distribution) so the
  overall distribution is realistically right-skewed rather than uniform.
- Risk_Label is derived via a weighted rule-based scoring formula (not random), so the
  dataset contains genuine, learnable signal for the ML models trained in `ml/train_model.py`.
