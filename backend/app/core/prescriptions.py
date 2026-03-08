from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

if TYPE_CHECKING:
	from app.models.doctor import Doctor
	from app.models.doctor_intervention import DoctorIntervention
	from app.models.user import User


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


def _draw_info_chip(pdf: canvas.Canvas, x: float, y: float, label: str, value: str, width: float, fill_color: str):
	pdf.setFillColor(colors.HexColor(fill_color))
	pdf.roundRect(x, y - 18, width, 20, 10, stroke=0, fill=1)
	pdf.setFillColor(colors.white)
	pdf.setFont('Helvetica-Bold', 8)
	pdf.drawString(x + 8, y - 5, label.upper())
	pdf.setFont('Helvetica', 8)
	pdf.drawRightString(x + width - 8, y - 5, value[:24])


def _draw_signature_block(pdf: canvas.Canvas, x: float, y: float, prescription: dict):
	pdf.setStrokeColor(colors.HexColor('#cbd5e1'))
	pdf.setFillColor(colors.HexColor('#f8fafc'))
	pdf.roundRect(x, y - 68, 240, 60, 14, stroke=1, fill=1)
	pdf.setFillColor(colors.HexColor('#475569'))
	pdf.setFont('Helvetica-Bold', 9)
	pdf.drawString(x + 12, y - 18, 'Digitally Signed By')
	pdf.setFillColor(colors.HexColor('#0f172a'))
	pdf.setFont('Helvetica-Oblique', 15)
	pdf.drawString(x + 12, y - 38, prescription.get('doctor_name') or 'Treating clinician')
	pdf.setFont('Helvetica', 8)
	pdf.setFillColor(colors.HexColor('#64748b'))
	pdf.drawString(x + 12, y - 54, f"License {prescription.get('doctor_license_number') or 'N/A'}")
	pdf.drawRightString(x + 228, y - 54, prescription.get('verification_id') or 'RX')


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
	y = height - 48
	brand_name = prescription.get('doctor_institution') or 'NeuroBloom Digital Clinic'
	status = prescription.get('status') or 'active'
	status_label = status.replace('_', ' ').title()
	status_color = '#0f766e' if status == 'active' else ('#b91c1c' if status == 'cancelled' else '#475569')

	pdf.setTitle(f"Prescription {prescription.get('verification_id')}")
	pdf.setStrokeColor(colors.HexColor('#cbd5e1'))
	pdf.setFillColor(colors.HexColor('#0f766e'))
	pdf.roundRect(36, height - 120, width - 72, 68, 18, stroke=0, fill=1)
	pdf.setFillColor(colors.HexColor('#14b8a6'))
	pdf.circle(width - 92, height - 87, 18, stroke=0, fill=1)
	pdf.setFillColor(colors.white)
	pdf.setFillColor(colors.white)
	pdf.setFont('Helvetica-Bold', 18)
	pdf.drawString(52, height - 78, brand_name[:42])
	pdf.setFont('Helvetica', 10)
	pdf.drawString(52, height - 94, 'Digital Prescription Record')
	pdf.drawString(52, height - 108, 'NeuroBloom clinical prescribing workflow')
	_draw_info_chip(pdf, 360, height - 68, 'Status', status_label, 90, status_color)
	_draw_info_chip(pdf, 456, height - 68, 'Version', f"V{prescription.get('version_number') or 1}", 72, '#1d4ed8')
	y = height - 146

	pdf.setFillColor(colors.HexColor('#111827'))
	pdf.setFont('Helvetica-Bold', 11)
	pdf.drawString(40, y, 'Doctor')
	pdf.drawString(width / 2, y, 'Patient')
	y -= 18

	pdf.setFont('Helvetica', 10)
	pdf.drawString(40, y, prescription.get('doctor_name') or 'Treating clinician')
	pdf.drawString(width / 2, y, prescription.get('patient_name') or 'Patient')
	y -= 14
	pdf.drawString(40, y, f"License: {prescription.get('doctor_license_number') or 'Not provided'}")
	pdf.drawString(width / 2, y, f"Diagnosis: {prescription.get('diagnosis') or 'Not recorded'}")
	y -= 14
	pdf.drawString(40, y, f"Institution: {prescription.get('doctor_institution') or 'NeuroBloom Clinic'}")
	pdf.drawString(width / 2, y, f"Issued: {format_pdf_date(prescription.get('created_at'))}")
	y -= 14
	pdf.drawString(40, y, f"Specialization: {prescription.get('doctor_specialization') or 'Clinician'}")
	pdf.drawString(width / 2, y, f"Prescription ID: {prescription.get('verification_id')}")
	y -= 24

	pdf.setStrokeColor(colors.HexColor('#dbe4ee'))
	pdf.line(40, y, width - 40, y)
	y -= 20

	pdf.setFont('Helvetica-Bold', 12)
	pdf.drawString(40, y, prescription.get('title') or 'Prescription')
	pdf.setFont('Helvetica', 10)
	pdf.drawRightString(width - 40, y, f"Version {prescription.get('version_number') or 1}")
	y -= 18
	y = _draw_wrapped_text(pdf, prescription.get('summary'), 40, y, width - 80)
	y -= 8

	if status != 'active':
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
	y -= 18

	medications = prescription.get('medications') or []
	if medications:
		for index, medication in enumerate(medications, start=1):
			pdf.setFillColor(colors.HexColor('#f8fafc'))
			pdf.roundRect(40, y - 54, width - 80, 50, 12, stroke=1, fill=1)
			pdf.setFillColor(colors.HexColor('#111827'))
			pdf.setFont('Helvetica-Bold', 10)
			pdf.drawString(52, y - 16, f"{index}. {medication.get('name') or 'Medication'}")
			pdf.setFont('Helvetica', 9)
			pdf.drawString(52, y - 30, f"Dosage: {medication.get('dosage') or '-'}")
			pdf.drawString(190, y - 30, f"Frequency: {medication.get('frequency') or '-'}")
			pdf.drawString(370, y - 30, f"Duration: {medication.get('duration') or '-'}")
			instruction = medication.get('instructions') or 'Follow doctor instructions.'
			y = _draw_wrapped_text(pdf, f"Instructions: {instruction}", 52, y - 44, width - 110, font_size=8, leading=10)
			y -= 12
	else:
		y = _draw_wrapped_text(pdf, 'No medication items were recorded. Review lifestyle plan and instructions below.', 40, y, width - 80)
		y -= 10

	pdf.setFont('Helvetica-Bold', 11)
	pdf.drawString(40, y, 'Patient Instructions')
	y -= 16
	pdf.setFont('Helvetica', 10)
	y = _draw_wrapped_text(pdf, prescription.get('patient_instructions'), 40, y, width - 80)
	y -= 10

	lifestyle_plan = prescription.get('lifestyle_plan') or []
	if lifestyle_plan:
		pdf.setFont('Helvetica-Bold', 11)
		pdf.drawString(40, y, 'Lifestyle Recommendations')
		y -= 16
		pdf.setFont('Helvetica', 10)
		for item in lifestyle_plan:
			y = _draw_wrapped_text(pdf, f"- {item}", 46, y, width - 86)
			y -= 4

	if prescription.get('follow_up_plan'):
		pdf.setFont('Helvetica-Bold', 11)
		pdf.drawString(40, y, 'Follow-up Plan')
		y -= 16
		pdf.setFont('Helvetica', 10)
		y = _draw_wrapped_text(pdf, prescription.get('follow_up_plan'), 40, y, width - 80)
		y -= 8

	if prescription.get('clinician_notes'):
		pdf.setFont('Helvetica-Bold', 11)
		pdf.drawString(40, y, 'Clinician Notes')
		y -= 16
		pdf.setFont('Helvetica', 10)
		y = _draw_wrapped_text(pdf, prescription.get('clinician_notes'), 40, y, width - 80)
		y -= 8

	_draw_signature_block(pdf, 40, 90, prescription)

	pdf.line(40, 96, width - 40, 96)
	pdf.setFont('Helvetica', 9)
	pdf.setFillColor(colors.HexColor('#475569'))
	pdf.drawString(40, 78, 'This prescription is issued digitally and must be validated by the treating physician.')
	pdf.drawString(40, 62, f"Digital verification: {prescription.get('verification_id')}")
	pdf.drawRightString(width - 40, 62, f"Generated: {format_pdf_date(datetime.utcnow())}")
	pdf.drawString(40, 44, f"Signature: {prescription.get('doctor_name') or 'Treating clinician'}")
	pdf.drawRightString(width - 40, 44, brand_name[:38])

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