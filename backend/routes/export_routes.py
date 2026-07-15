"""
routes/export_routes.py
=========================
Report export endpoints. Supports both CSV (raw tabular data) and PDF
(formatted, presentable report) for:
    - An individual student's attendance report ("Download Report")
    - A faculty-facing class/department summary report ("Export Report")
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy.orm import Session

from auth import get_current_user, require_faculty
from database import Student, User, get_db
from models import ExportFormatEnum
from routes.faculty_routes import _base_student_query, _compute_worst_case_risk, _department_stats, _subject_stats
from routes.prediction_routes import _resolve_target_student
from routes.student_routes import _get_attendance_records

router = APIRouter(prefix="/api/export", tags=["Export"])


# --------------------------------------------------------------------------
# PDF styling helpers
# --------------------------------------------------------------------------

class ReportPDF(FPDF):
    """A minimal, clean PDF report layout shared by both export types."""

    def header(self) -> None:
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(37, 99, 235)  # brand blue
        self.cell(0, 10, "Smart Attendance Pattern Analyzer", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}", ln=True, align="C")
        self.ln(4)
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 30, 30)
        self.cell(0, 9, title, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def key_value_row(self, key: str, value: str) -> None:
        self.set_font("Helvetica", "B", 10)
        self.cell(55, 7, key, border=0)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 7, str(value), ln=True)

    def table_header(self, headers: list[str], widths: list[int]) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        for header, width in zip(headers, widths):
            self.cell(width, 8, header, border=1, align="C", fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)

    def table_row(self, values: list, widths: list[int], fill: bool = False) -> None:
        self.set_font("Helvetica", "", 8)
        self.set_fill_color(245, 247, 250)
        for value, width in zip(values, widths):
            self.cell(width, 7, str(value), border=1, align="C", fill=fill)
        self.ln()


# --------------------------------------------------------------------------
# Student report
# --------------------------------------------------------------------------

def _build_student_csv(student: Student, records) -> io.StringIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Student Attendance Report"])
    writer.writerow(["Student Code", student.student_code])
    writer.writerow(["Name", student.name])
    writer.writerow(["Department", student.department])
    writer.writerow(["Semester", student.semester])
    writer.writerow([])
    writer.writerow([
        "Subject", "Total Classes", "Classes Attended", "Attendance %",
        "Previous Attendance %", "Leaves Taken", "Internal Marks", "Risk Label",
    ])
    for r in records:
        writer.writerow([
            r.subject.name, r.total_classes, r.classes_attended, r.attendance_percentage,
            r.previous_attendance_percentage, r.leaves_taken, r.internal_marks, r.risk_label,
        ])
    buffer.seek(0)
    return buffer


def _build_student_pdf(student: Student, records) -> io.BytesIO:
    pdf = ReportPDF()
    pdf.add_page()

    pdf.section_title("Student Information")
    pdf.key_value_row("Student Code:", student.student_code)
    pdf.key_value_row("Name:", student.name)
    pdf.key_value_row("Department:", student.department)
    pdf.key_value_row("Semester:", str(student.semester))
    pdf.key_value_row("Gender:", student.gender or "-")
    pdf.ln(4)

    overall = round(sum(r.attendance_percentage for r in records) / len(records), 2) if records else 0.0
    pdf.section_title("Overall Attendance")
    pdf.key_value_row("Overall Attendance %:", f"{overall}%")
    pdf.key_value_row("Status:", "Below Requirement (< 75%)" if overall < 75 else "Meets Requirement")
    pdf.ln(4)

    pdf.section_title("Subject-wise Attendance")
    headers = ["Subject", "Total", "Attended", "Attendance %", "Leaves", "Marks", "Risk"]
    widths = [45, 20, 22, 28, 20, 20, 35]
    pdf.table_header(headers, widths)
    for i, r in enumerate(records):
        pdf.table_row(
            [r.subject.name, r.total_classes, r.classes_attended, f"{r.attendance_percentage}%",
             r.leaves_taken, r.internal_marks, r.risk_label or "-"],
            widths, fill=(i % 2 == 0),
        )

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer


@router.get("/student-report")
def export_student_report(
    student_code: Optional[str] = Query(None, description="Required for faculty; omitted for a student's own report"),
    format: ExportFormatEnum = Query(ExportFormatEnum.pdf),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Export a single student's attendance report as PDF or CSV. Students
    may only export their own report; faculty/admin may export any
    student's report by passing `student_code`.
    """
    student = _resolve_target_student(db, current_user, student_code)
    if student is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid student_code is required")

    records = _get_attendance_records(db, student.id)
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No attendance data available for this student")

    filename_base = f"attendance_report_{student.student_code}"

    if format == ExportFormatEnum.csv:
        buffer = _build_student_csv(student, records)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.csv"'},
        )
    else:
        buffer = _build_student_pdf(student, records)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
        )


# --------------------------------------------------------------------------
# Faculty report
# --------------------------------------------------------------------------

def _build_faculty_csv(students: list[Student], risk_map: dict) -> io.StringIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Faculty Attendance Summary Report"])
    writer.writerow([])
    writer.writerow(["Student Code", "Name", "Department", "Semester", "Overall Attendance %", "Trend", "Risk Level"])
    for s in students:
        writer.writerow([
            s.student_code, s.name, s.department, s.semester,
            s.overall_attendance_percentage, s.trend, risk_map.get(s.id, "-"),
        ])
    buffer.seek(0)
    return buffer


def _build_faculty_pdf(
    students: list[Student],
    risk_map: dict,
    department_stats,
    subject_stats,
    department_filter: Optional[str],
) -> io.BytesIO:
    pdf = ReportPDF()
    pdf.add_page()

    pdf.section_title("Report Scope")
    pdf.key_value_row("Department:", department_filter or "All Departments")
    pdf.key_value_row("Total Students:", str(len(students)))
    below_75 = sum(1 for s in students if (s.overall_attendance_percentage or 0) < 75)
    pdf.key_value_row("Students Below 75%:", str(below_75))
    pdf.ln(4)

    pdf.section_title("Department-wise Attendance")
    headers = ["Department", "Avg Attendance %", "Students", "Below 75%"]
    widths = [70, 40, 30, 30]
    pdf.table_header(headers, widths)
    for i, d in enumerate(department_stats):
        pdf.table_row([d.department, f"{d.average_attendance}%", d.total_students, d.below_75_count], widths, fill=(i % 2 == 0))
    pdf.ln(4)

    pdf.section_title("Subject-wise Attendance")
    headers2 = ["Subject", "Avg Attendance %", "Enrolled"]
    widths2 = [80, 45, 45]
    pdf.table_header(headers2, widths2)
    for i, sub in enumerate(subject_stats):
        pdf.table_row([sub.subject_name, f"{sub.average_attendance}%", sub.total_enrolled], widths2, fill=(i % 2 == 0))
    pdf.ln(4)

    pdf.add_page()
    pdf.section_title("Student Roster (sorted by attendance, lowest first)")
    headers3 = ["Code", "Name", "Dept", "Sem", "Attendance %", "Risk"]
    widths3 = [25, 50, 35, 15, 30, 35]
    pdf.table_header(headers3, widths3)
    sorted_students = sorted(students, key=lambda s: s.overall_attendance_percentage or 0)
    for i, s in enumerate(sorted_students[:60]):  # cap rows to keep the PDF a reasonable length
        pdf.table_row(
            [s.student_code, s.name[:22], s.department[:16], s.semester,
             f"{s.overall_attendance_percentage}%", risk_map.get(s.id, "-")],
            widths3, fill=(i % 2 == 0),
        )

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer


@router.get("/faculty-report")
def export_faculty_report(
    department: Optional[str] = Query(None),
    format: ExportFormatEnum = Query(ExportFormatEnum.pdf),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export a faculty-facing class/department summary report as PDF or CSV."""
    students = _base_student_query(db, department=department).all()
    if not students:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No students found for this filter")

    risk_map = _compute_worst_case_risk(db, student_ids=[s.id for s in students])
    filename_base = f"faculty_report_{department or 'all_departments'}".replace(" ", "_")

    if format == ExportFormatEnum.csv:
        buffer = _build_faculty_csv(students, risk_map)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.csv"'},
        )
    else:
        department_stats = _department_stats(db)
        if department:
            department_stats = [d for d in department_stats if d.department == department]
        subject_stats = _subject_stats(db, department=department)
        buffer = _build_faculty_pdf(students, risk_map, department_stats, subject_stats, department)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
        )
