from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.models.request import PurchaseRequest


class PdfService:
    def generate_evidence(self, purchase_request: PurchaseRequest) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        _, height = letter
        y = height - 50

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, "Evidencia de Solicitud de Compra")
        y -= 40

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Datos de la solicitud")
        y -= 25

        pdf.setFont("Helvetica", 10)
        request_lines = [
            f"Request ID: {purchase_request.request_id}",
            f"Titulo: {purchase_request.title}",
            f"Descripcion: {purchase_request.description}",
            f"Monto: {purchase_request.amount}",
            f"Solicitante: {purchase_request.requester_name}",
            f"Fecha de creacion: {purchase_request.created_at}",
            f"Estado: {purchase_request.status.value}",
        ]
        for line in request_lines:
            pdf.drawString(50, y, line)
            y -= 18

        y -= 15
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Aprobaciones")
        y -= 25

        pdf.setFont("Helvetica", 10)
        for approver in purchase_request.approvers:
            lines = [
                f"Nombre: {approver.name}",
                f"Email: {approver.email}",
                f"Status: {approver.status.value}",
                f"Signed at: {approver.signed_at or ''}",
                f"Firma simulada: {approver.name} + {approver.signed_at or ''}",
            ]
            for line in lines:
                pdf.drawString(50, y, line)
                y -= 16
            y -= 10

            if y < 80:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 50

        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()
