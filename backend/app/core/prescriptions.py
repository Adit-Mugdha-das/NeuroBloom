from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

if TYPE_CHECKING:
	from app.models.doctor import Doctor
	from app.models.doctor_intervention import DoctorIntervention
	from app.models.user import User


PAGE_MARGIN = 40
RESERVED_FOOTER_HEIGHT = 98
FOOTER_LINE_Y = 54
SIGNATURE_TOP_Y = 122
LOGO_PATH = Path(__file__).resolve().parents[3] / 'frontend-svelte' / 'images' / 'logo.png'


def parse_prescription_data(value: Optional[str]) -> Optional[dict]:
	if not value:
		return None

	try:
		return json.loads(value)
	except json.JSONDecodeError:
		return None


def build_prescription_verification_id(intervention_id: Optional[int]) -> str:
	if intervention_id is None:
		return 'RX-PENDING'
	return f'RX-{intervention_id:06d}'


def serialize_prescription_intervention(
	intervention: 'DoctorIntervention',
	doctor: Optional['Doctor'] = None,
	patient: Optional['User'] = None,
	diagnosis: Optional[str] = None
):
	data = parse_prescription_data(intervention.intervention_data) or {}
	medications = data.get('medications') or []
	lifestyle_plan = data.get('lifestyle_plan') or []
	verification_id = data.get('verification_id') or build_prescription_verification_id(intervention.id)
	prescription_group_id = data.get('prescription_group_id') or intervention.id
	version_number = int(data.get('version_number') or 1)

	return {
		'id': intervention.id,
		'type': intervention.intervention_type,
		'title': data.get('title') or intervention.description,
		'summary': data.get('summary') or intervention.description,
		'patient_instructions': data.get('patient_instructions') or intervention.description,
		'clinician_notes': data.get('clinician_notes'),
		'status': data.get('status') or 'active',
		'valid_from': data.get('valid_from'),
		'valid_until': data.get('valid_until'),
		'review_date': data.get('review_date'),
		'follow_up_plan': data.get('follow_up_plan'),
		'medications': medications,
		'lifestyle_plan': lifestyle_plan,
		'medication_count': len(medications),
		'created_at': intervention.created_at,
		'doctor_id': intervention.doctor_id,
		'doctor_name': doctor.full_name if doctor and doctor.full_name else None,
		'doctor_license_number': doctor.license_number if doctor else None,
		'doctor_institution': doctor.institution if doctor else None,
		'doctor_specialization': doctor.specialization if doctor else None,
		'patient_id': intervention.patient_id,
		'patient_name': patient.full_name if patient and patient.full_name else (patient.email if patient else None),
		'diagnosis': diagnosis or data.get('diagnosis'),
		'verification_id': verification_id,
		'prescription_group_id': prescription_group_id,
		'version_number': version_number,
		'replaces_prescription_id': data.get('replaces_prescription_id'),
		'retired_at': data.get('retired_at'),
		'retired_reason': data.get('retired_reason'),
		'is_revision': version_number > 1,
	}


def _draw_signature_block(pdf: canvas.Canvas, x: float, y: float, prescription: dict):
	pdf.setStrokeColor(colors.HexColor('#cbd5e1'))
	pdf.setFillColor(colors.HexColor('#f8fafc'))
	pdf.roundRect(x, y - 52, 240, 44, 14, stroke=1, fill=1)
	pdf.setFillColor(colors.HexColor('#475569'))
	pdf.setFont('Helvetica-Bold', 8)
	pdf.drawString(x + 12, y - 16, 'Digitally Signed By')
	pdf.setFillColor(colors.HexColor('#0f172a'))
	pdf.setFont('Helvetica-Oblique', 13)
	pdf.drawString(x + 12, y - 30, prescription.get('doctor_name') or 'Treating clinician')
	pdf.setFont('Helvetica', 8)
	pdf.setFillColor(colors.HexColor('#64748b'))
	pdf.drawString(x + 12, y - 42, f"License {prescription.get('doctor_license_number') or 'N/A'}")
	pdf.drawRightString(x + 228, y - 42, prescription.get('verification_id') or 'RX')


def _measure_wrapped_lines(text: Optional[str], font_name: str, font_size: int, max_width: float):
	content = text or '-'
	return simpleSplit(content, font_name, font_size, max_width) or ['-']


def _ensure_page_space(
	pdf: canvas.Canvas,
	y: float,
	required_height: float,
	width: float,
	height: float,
	prescription: dict,
	page_number: int,
):
	if y - required_height >= PAGE_MARGIN + RESERVED_FOOTER_HEIGHT:
		return y, page_number

	pdf.showPage()
	page_number += 1
	return _draw_page_header(pdf, width, height, prescription, page_number), page_number


def _draw_logo(pdf: canvas.Canvas, x: float, y: float, size: float):
	if not LOGO_PATH.exists():
		return False

	pdf.setFillColor(colors.white)
	pdf.roundRect(x, y - size, size, size, 14, stroke=0, fill=1)
	pdf.drawImage(ImageReader(str(LOGO_PATH)), x + 5, y - size + 5, width=size - 10, height=size - 10, mask='auto', preserveAspectRatio=True)
	return True


def _draw_page_header(pdf: canvas.Canvas, width: float, height: float, prescription: dict, page_number: int) -> float:
	brand_name = prescription.get('doctor_institution') or 'NeuroBloom Digital Clinic'

	pdf.setStrokeColor(colors.HexColor('#cbd5e1'))
	pdf.setFillColor(colors.HexColor('#0f766e'))

	if page_number == 1:
		pdf.roundRect(36, height - 108, width - 72, 56, 18, stroke=0, fill=1)
		pdf.setFillColor(colors.HexColor('#14b8a6'))
		pdf.circle(width - 92, height - 80, 15, stroke=0, fill=1)
		logo_drawn = _draw_logo(pdf, 52, height - 60, 38)
		text_x = 100 if logo_drawn else 52
		pdf.setFillColor(colors.white)
		pdf.setFont('Helvetica-Bold', 17)
		pdf.drawString(text_x, height - 74, brand_name[:40])
		pdf.setFont('Helvetica', 9)
		pdf.drawString(text_x, height - 89, 'Digital Prescription Record')
		pdf.drawString(text_x, height - 102, 'NeuroBloom clinical prescribing workflow')
		return height - 128

	pdf.roundRect(36, height - 76, width - 72, 28, 14, stroke=0, fill=1)
	logo_drawn = _draw_logo(pdf, 50, height - 48, 20)
	text_x = 82 if logo_drawn else 50
	pdf.setFillColor(colors.white)
	pdf.setFont('Helvetica-Bold', 11)
	pdf.drawString(text_x, height - 60, (prescription.get('title') or 'Prescription')[:50])
	pdf.setFont('Helvetica', 8)
	pdf.drawRightString(width - 50, height - 60, f"Page {page_number}")
	return height - 92


def _draw_footer(pdf: canvas.Canvas, width: float, prescription: dict, brand_name: str):
	pdf.line(40, FOOTER_LINE_Y, width - 40, FOOTER_LINE_Y)
	pdf.setFont('Helvetica', 8)
	pdf.setFillColor(colors.HexColor('#475569'))
	pdf.drawString(40, 38, f"Digital verification: {prescription.get('verification_id')}")
	pdf.drawRightString(width - 40, 38, f"Generated: {format_pdf_date(datetime.utcnow())}")


def _draw_labeled_text(pdf: canvas.Canvas, label: str, value: Optional[str], x: float, y: float, max_width: float, *, bold_first_line: bool = False):
	font_name = 'Helvetica-Bold' if bold_first_line else 'Helvetica'
	lines = _measure_wrapped_lines(value, font_name, 10, max_width)
	pdf.setFillColor(colors.HexColor('#111827'))
	pdf.setFont(font_name, 10)
	for line in lines:
		pdf.drawString(x, y, line)
		y -= 12

	text = f"{label}: {value or '-'}"
	lines = _measure_wrapped_lines(text, 'Helvetica', 9, max_width)
	pdf.setFont('Helvetica', 9)
	pdf.setFillColor(colors.HexColor('#374151'))
	for line in lines:
		pdf.drawString(x, y, line)
		y -= 12
	return y


def _draw_key_value_text(pdf: canvas.Canvas, label: str, value: Optional[str], x: float, y: float, max_width: float):
	text = f"{label}: {value or '-'}"
	lines = _measure_wrapped_lines(text, 'Helvetica', 9, max_width)
	pdf.setFont('Helvetica', 9)
	pdf.setFillColor(colors.HexColor('#374151'))
	for line in lines:
		pdf.drawString(x, y, line)
		y -= 12
	return y


def _draw_bullets(pdf: canvas.Canvas, items: list[str], x: float, y: float, max_width: float):
	for item in items:
		lines = _measure_wrapped_lines(f"- {item}", 'Helvetica', 10, max_width)
		pdf.setFont('Helvetica', 10)
		pdf.setFillColor(colors.HexColor('#111827'))
		for line in lines:
			pdf.drawString(x, y, line)
			y -= 14
		y -= 2
	return y


def _draw_wrapped_text(
	pdf: canvas.Canvas,
	text: Optional[str],
	x: float,
	y: float,
	max_width: float,
	font_name: str = 'Helvetica',
	font_size: int = 10,
	leading: int = 14,
):
	content = text or '-'
	lines = simpleSplit(content, font_name, font_size, max_width) or ['-']
	pdf.setFont(font_name, font_size)
	for line in lines:
		pdf.drawString(x, y, line)
		y -= leading
	return y


def generate_prescription_pdf_bytes(prescription: dict) -> bytes:
	buffer = io.BytesIO()
	pdf = canvas.Canvas(buffer, pagesize=A4)
	width, height = A4
	brand_name = prescription.get('doctor_institution') or 'NeuroBloom Digital Clinic'
	page_number = 1

	pdf.setTitle(f"Prescription {prescription.get('verification_id')}")
	y = _draw_page_header(pdf, width, height, prescription, page_number)

	pdf.setFillColor(colors.HexColor('#111827'))
	pdf.setFont('Helvetica-Bold', 11)
	pdf.drawString(40, y, 'Doctor')
	pdf.drawString(width / 2, y, 'Patient')
	y -= 18

	left_x = 40
	right_x = width / 2
	column_width = width / 2 - 52
	left_y = _draw_wrapped_text(
		pdf,
		prescription.get('doctor_name') or 'Treating clinician',
		left_x,
		y,
		column_width,
		font_name='Helvetica-Bold',
		font_size=10,
		leading=12,
	)
	left_y = _draw_key_value_text(pdf, 'License', prescription.get('doctor_license_number') or 'Not provided', left_x, left_y, column_width)
	left_y = _draw_key_value_text(pdf, 'Institution', prescription.get('doctor_institution') or 'NeuroBloom Clinic', left_x, left_y, column_width)
	left_y = _draw_key_value_text(pdf, 'Specialization', prescription.get('doctor_specialization') or 'Clinician', left_x, left_y, column_width)

	right_y = _draw_wrapped_text(
		pdf,
		prescription.get('patient_name') or 'Patient',
		right_x,
		y,
		column_width,
		font_name='Helvetica-Bold',
		font_size=10,
		leading=12,
	)
	right_y = _draw_key_value_text(pdf, 'Diagnosis', prescription.get('diagnosis') or 'Not recorded', right_x, right_y, column_width)
	right_y = _draw_key_value_text(pdf, 'Issued', format_pdf_date(prescription.get('created_at')), right_x, right_y, column_width)
	y = min(left_y, right_y) - 12

	pdf.setStrokeColor(colors.HexColor('#dbe4ee'))
	pdf.line(40, y, width - 40, y)
	y -= 16

	y, page_number = _ensure_page_space(pdf, y, 66, width, height, prescription, page_number)
	pdf.setFont('Helvetica-Bold', 12)
	pdf.drawString(40, y, prescription.get('title') or 'Prescription')
	y -= 18
	y = _draw_wrapped_text(pdf, prescription.get('summary'), 40, y, width - 80)
	y -= 8

	status = prescription.get('status') or 'active'
	status_label = status.replace('_', ' ').title()
	status_color = '#0f766e' if status == 'active' else ('#b91c1c' if status == 'cancelled' else '#475569')
	if status != 'active':
		y, page_number = _ensure_page_space(pdf, y, 52, width, height, prescription, page_number)
		pdf.setFillColor(colors.HexColor('#fff7ed' if status == 'inactive' else '#fef2f2'))
		pdf.roundRect(40, y - 34, width - 80, 28, 12, stroke=0, fill=1)
		pdf.setFillColor(colors.HexColor(status_color))
		pdf.setFont('Helvetica-Bold', 10)
		pdf.drawString(52, y - 18, f"Prescription status: {status_label}")
		if prescription.get('retired_reason'):
			pdf.setFont('Helvetica', 8)
			pdf.drawRightString(width - 52, y - 18, str(prescription.get('retired_reason'))[:56])
		y -= 42

	pdf.setFont('Helvetica-Bold', 11)
	pdf.drawString(40, y, 'Medication Plan')
	y -= 16

	medications = prescription.get('medications') or []
	if medications:
		for index, medication in enumerate(medications, start=1):
			instruction = medication.get('instructions') or 'Follow doctor instructions.'
			instruction_lines = _measure_wrapped_lines(f"Instructions: {instruction}", 'Helvetica', 8, width - 110)
			box_height = 34 + (len(instruction_lines) * 10)
			y, page_number = _ensure_page_space(pdf, y, box_height + 14, width, height, prescription, page_number)
			pdf.setFillColor(colors.HexColor('#f8fafc'))
			pdf.roundRect(40, y - box_height, width - 80, box_height - 4, 12, stroke=1, fill=1)
			pdf.setFillColor(colors.HexColor('#111827'))
			pdf.setFont('Helvetica-Bold', 10)
			pdf.drawString(52, y - 14, f"{index}. {medication.get('name') or 'Medication'}")
			pdf.setFont('Helvetica', 9)
			pdf.drawString(52, y - 26, f"Dosage: {medication.get('dosage') or '-'}")
			pdf.drawString(190, y - 26, f"Frequency: {medication.get('frequency') or '-'}")
			pdf.drawString(370, y - 26, f"Duration: {medication.get('duration') or '-'}")
			y = _draw_wrapped_text(pdf, f"Instructions: {instruction}", 52, y - 38, width - 110, font_size=8, leading=10)
			y -= 8
	else:
		y, page_number = _ensure_page_space(pdf, y, 36, width, height, prescription, page_number)
		y = _draw_wrapped_text(pdf, 'No medication items were recorded. Review lifestyle plan and instructions below.', 40, y, width - 80)
		y -= 10

	y, page_number = _ensure_page_space(pdf, y, 48, width, height, prescription, page_number)
	pdf.setFont('Helvetica-Bold', 11)
	pdf.drawString(40, y, 'Patient Instructions')
	y -= 16
	pdf.setFont('Helvetica', 10)
	y = _draw_wrapped_text(pdf, prescription.get('patient_instructions'), 40, y, width - 80)
	y -= 10

	lifestyle_plan = prescription.get('lifestyle_plan') or []
	if lifestyle_plan:
		bullet_height = sum(max(1, len(_measure_wrapped_lines(f"- {item}", 'Helvetica', 10, width - 86))) * 14 + 2 for item in lifestyle_plan)
		y, page_number = _ensure_page_space(pdf, y, 24 + bullet_height, width, height, prescription, page_number)
		pdf.setFont('Helvetica-Bold', 11)
		pdf.drawString(40, y, 'Lifestyle Recommendations')
		y -= 16
		y = _draw_bullets(pdf, lifestyle_plan, 46, y, width - 86)

	if prescription.get('follow_up_plan'):
		y, page_number = _ensure_page_space(pdf, y, 52, width, height, prescription, page_number)
		pdf.setFont('Helvetica-Bold', 11)
		pdf.drawString(40, y, 'Follow-up Plan')
		y -= 16
		pdf.setFont('Helvetica', 10)
		y = _draw_wrapped_text(pdf, prescription.get('follow_up_plan'), 40, y, width - 80)
		y -= 8

	if prescription.get('clinician_notes'):
		y, page_number = _ensure_page_space(pdf, y, 52, width, height, prescription, page_number)
		pdf.setFont('Helvetica-Bold', 11)
		pdf.drawString(40, y, 'Clinician Notes')
		y -= 16
		pdf.setFont('Helvetica', 10)
		y = _draw_wrapped_text(pdf, prescription.get('clinician_notes'), 40, y, width - 80)
		y -= 8

	y, page_number = _ensure_page_space(pdf, y, RESERVED_FOOTER_HEIGHT - 10, width, height, prescription, page_number)
	_draw_signature_block(pdf, 40, SIGNATURE_TOP_Y, prescription)
	_draw_footer(pdf, width, prescription, brand_name)

	pdf.save()
	buffer.seek(0)
	return buffer.read()


def format_pdf_date(value) -> str:
	if isinstance(value, str):
		try:
			value = datetime.fromisoformat(value.replace('Z', '+00:00'))
		except ValueError:
			return value

	if isinstance(value, datetime):
		return value.strftime('%d %b %Y %H:%M')

	return '-'