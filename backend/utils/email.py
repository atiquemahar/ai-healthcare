import resend
import os
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@yourdomain.com")


def send_prescription_email(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    prescription_id: int,
    diagnosis: str,
    medications: list,
    follow_up_date: str = None,
    pdf_path: str = None,
) -> bool:
    """Send prescription email to patient with PDF attachment."""

    meds_html = "".join([
        f"<li><strong>{m.get('drug_name')}</strong> {m.get('dosage')} — {m.get('frequency')} for {m.get('duration')}</li>"
        for m in (medications or [])
    ])

    follow_up_html = f"<p><strong>Follow-up:</strong> {follow_up_date}</p>" if follow_up_date else ""

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 30px;">
      <div style="background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
        <h2 style="margin:0">Your Prescription is Ready</h2>
      </div>
      <div style="border: 1px solid #e2e8f0; border-top: none; padding: 25px; border-radius: 0 0 8px 8px;">
        <p>Dear {patient_name},</p>
        <p>Your prescription from <strong>{doctor_name}</strong> is attached to this email.</p>

        <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0;">
          <p style="margin:0 0 8px 0"><strong>Diagnosis:</strong> {diagnosis}</p>
          <strong>Medications:</strong>
          <ul style="margin: 8px 0; padding-left: 20px;">
            {meds_html}
          </ul>
          {follow_up_html}
        </div>

        <p style="color: #6b7280; font-size: 13px;">
          Please take your medications as directed. Contact the clinic if you have any questions.
        </p>
        <p style="color: #9ca3af; font-size: 12px; margin-top: 20px;">
          This is an AI-assisted prescription system. Always consult your doctor with any concerns.
        </p>
      </div>
    </div>
    """

    try:
        params = {
            "from": FROM_EMAIL,
            "to": [patient_email],
            "subject": f"Your Prescription from {doctor_name}",
            "html": html_body,
        }

        # Attach PDF if path provided
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                import base64
                pdf_data = base64.b64encode(f.read()).decode()
            params["attachments"] = [{
                "filename": f"prescription_{prescription_id}.pdf",
                "content": pdf_data,
            }]

        resend.Emails.send(params)
        return True

    except Exception as e:
        print(f"Email send error: {e}")
        return False
