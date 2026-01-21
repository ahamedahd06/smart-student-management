# Test Plan

## Objectives
- Verify core modules (student registry, attendance, emotion detection, dashboard).
- Validate error handling and data integrity.
- Ensure outputs are clear and reproducible for evaluation.

## Scope
- Functional tests of UI and database operations.
- Emotion model inference with a valid face image.
- Edge cases: missing model, non-face images, empty fields.

## Environment
- OS: Windows 10/11 or Linux
- Python 3.10+
- Packages: per `requirements.txt`
- Browser: Chrome/Edge/Firefox

## Test Cases

| ID | Test Case | Steps | Expected Result |
|---|---|---|---|
| TC-01 | Add student (valid) | Open Students tab, add student with ID + name | Student is saved and appears in list |
| TC-02 | Add student (missing ID) | Leave Student ID empty and submit | Error message, no record saved |
| TC-03 | Add student (duplicate ID) | Add same student ID twice | Error: "Student ID already exists" |
| TC-04 | Update student | Select student, change name, save | Updated values persist in table |
| TC-05 | Delete student | Select student, confirm delete | Student removed and logs deleted |
| TC-06 | Log attendance only | Save log without image | Log saved with attendance only |
| TC-07 | Emotion detection (valid face) | Upload a clear face, analyze | Emotion label + confidence displayed |
| TC-08 | Emotion detection (no face) | Upload non-face image | Error "No face detected", no emotion saved |
| TC-09 | Missing model file | Remove model file, upload image | Warning and log saved without emotion |
| TC-10 | Dashboard charts | Add multiple logs | Attendance + emotion charts render correctly |
| TC-11 | Risk scoring | Add logs with absences + negative emotions | Risk level becomes Medium/High per rules |
| TC-12 | Export CSV | Use Reports tab downloads | CSV files download with correct rows |
