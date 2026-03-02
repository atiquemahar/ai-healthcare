import os
from datetime import datetime


def generate_prescription_html(prescription, encounter, patient, doctor) -> str:
    """Build the HTML that gets converted to PDF."""

    medications_html = ""
    for i, med in enumerate(prescription.medications or [], 1):
        medications_html += f"""
        <div class="medication">
            <div class="med-number">{i}.</div>
            <div class="med-details">
                <strong>{med.get('drug_name', '')}</strong> — {med.get('dosage', '')}
                <br>
                <span class="med-meta">
                    {med.get('frequency', '')} &nbsp;|&nbsp;
                    Duration: {med.get('duration', '')}
                </span>
                {f"<br><span class='med-instruction'>{med.get('instructions', '')}</span>" if med.get('instructions') else ''}
            </div>
        </div>"""

    diagnosis_text = ""
    if encounter.diagnosis:
        diagnosis_text = ", ".join([d.get("condition_name", "") for d in encounter.diagnosis])

    follow_up = ""
    if prescription.follow_up_date:
        follow_up = f"""
        <div class="section">
            <div class="section-title">FOLLOW-UP</div>
            <p>{prescription.follow_up_date.strftime('%B %d, %Y')}</p>
            {f"<p class='followup-note'>{prescription.follow_up_notes}</p>" if prescription.follow_up_notes else ''}
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: #1a1a2e;
    padding: 40px;
    max-width: 750px;
    margin: auto;
  }}
  .header {{
    border-bottom: 3px solid #2563eb;
    padding-bottom: 20px;
    margin-bottom: 25px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }}
  .hospital-name {{
    font-size: 22px;
    font-weight: 700;
    color: #2563eb;
  }}
  .hospital-details {{
    font-size: 11px;
    color: #666;
    margin-top: 4px;
    line-height: 1.6;
  }}
  .rx-label {{
    font-size: 48px;
    color: #2563eb;
    font-weight: 200;
    line-height: 1;
  }}
  .doctor-section {{
    background: #f0f4ff;
    padding: 14px 18px;
    border-radius: 8px;
    margin-bottom: 20px;
  }}
  .doctor-name {{
    font-size: 16px;
    font-weight: 700;
    color: #1e3a8a;
  }}
  .doctor-meta {{
    font-size: 11px;
    color: #555;
    margin-top: 3px;
  }}
  .patient-section {{
    display: flex;
    justify-content: space-between;
    padding: 14px 18px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-bottom: 20px;
  }}
  .patient-name {{
    font-size: 15px;
    font-weight: 600;
  }}
  .patient-meta {{
    font-size: 11px;
    color: #555;
    margin-top: 4px;
    line-height: 1.8;
  }}
  .section {{
    margin-bottom: 20px;
  }}
  .section-title {{
    font-size: 11px;
    font-weight: 700;
    color: #2563eb;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-bottom: 1px solid #bfdbfe;
    padding-bottom: 5px;
    margin-bottom: 12px;
  }}
  .medication {{
    display: flex;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px dashed #e2e8f0;
  }}
  .med-number {{
    font-weight: 700;
    color: #2563eb;
    min-width: 20px;
  }}
  .med-details {{ flex: 1; }}
  .med-meta {{
    color: #555;
    font-size: 12px;
  }}
  .med-instruction {{
    color: #059669;
    font-style: italic;
    font-size: 11px;
  }}
  .instructions-text {{
    line-height: 1.8;
    color: #374151;
  }}
  .footer {{
    margin-top: 35px;
    padding-top: 20px;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .qr-placeholder {{
    width: 70px;
    height: 70px;
    border: 2px solid #cbd5e1;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: #999;
    text-align: center;
  }}
  .signature-section {{
    text-align: right;
  }}
  .signature-line {{
    border-bottom: 1px solid #374151;
    width: 200px;
    margin-bottom: 5px;
  }}
  .signature-name {{
    font-size: 12px;
    color: #374151;
  }}
  .disclaimer {{
    margin-top: 20px;
    font-size: 10px;
    color: #9ca3af;
    text-align: center;
    font-style: italic;
  }}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="hospital-name">Medical Center</div>
    <div class="hospital-details">
      123 Medical Street, City<br>
      Phone: +1-234-567-8900 &nbsp;|&nbsp; Email: info@medical.com
    </div>
  </div>
  <div class="rx-label">Rx</div>
</div>

<div class="doctor-section">
  <div class="doctor-name">{doctor.full_name}</div>
  <div class="doctor-meta">
    {doctor.specialization or 'General Physician'} &nbsp;|&nbsp; License: {doctor.license_number or 'N/A'}
  </div>
</div>

<div class="patient-section">
  <div>
    <div class="patient-name">{patient.full_name}</div>
    <div class="patient-meta">
      DOB: {patient.date_of_birth or 'N/A'}<br>
      Gender: {patient.gender or 'N/A'}<br>
      Phone: {patient.phone or 'N/A'}
    </div>
  </div>
  <div class="patient-meta" style="text-align:right">
    <strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}<br>
    <strong>Rx ID:</strong> RX-{prescription.id:06d}
  </div>
</div>

<div class="section">
  <div class="section-title">Diagnosis</div>
  <p>{diagnosis_text or 'See examination notes'}</p>
</div>

<div class="section">
  <div class="section-title">Prescribed Medications</div>
  {medications_html}
</div>

{f'''<div class="section">
  <div class="section-title">Instructions</div>
  <p class="instructions-text">{prescription.additional_instructions}</p>
</div>''' if prescription.additional_instructions else ''}

{follow_up}

<div class="footer">
  <div class="qr-placeholder">QR<br>Code</div>
  <div class="signature-section">
    <div class="signature-line"></div>
    <div class="signature-name">
      {doctor.full_name}<br>
      <span style="font-size:11px;color:#666">{doctor.specialization or ''} | Lic: {doctor.license_number or ''}</span>
    </div>
  </div>
</div>

<div class="disclaimer">
  This is a computer-generated prescription. AI-assisted — for informational purposes only.
  Always consult your physician with any questions.
</div>

</body>
</html>"""
    return html


def generate_prescription_pdf(prescription, encounter, patient, doctor) -> bytes:
    """Convert HTML prescription to PDF bytes using WeasyPrint."""
    try:
        from weasyprint import HTML
        html_content = generate_prescription_html(prescription, encounter, patient, doctor)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise


def save_pdf_locally(pdf_bytes: bytes, prescription_id: int) -> str:
    """
    Save PDF to local /tmp folder for MVP.
    In production: upload to S3 and return URL.
    Returns the file path / URL.
    """
    os.makedirs("pdfs", exist_ok=True)
    filename = f"pdfs/prescription_{prescription_id}.pdf"
    with open(filename, "wb") as f:
        f.write(pdf_bytes)
    return filename
