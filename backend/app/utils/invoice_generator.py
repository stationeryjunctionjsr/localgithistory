"""
Invoice PDF Generator for Orders
"""

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pydantic import Field

from app.models.base import CamelBaseModel
from app.models.schemas import PopulatedOrderResponse, Address
from app.models.payment import Payment


class SellerInvoiceInfo(CamelBaseModel):
    name: str = "Stationery Junction"
    company_name: str = ""
    gstin: str = ""
    address: Address = Field(default_factory=Address)

STATE_CODES = {
    "JAMMU AND KASHMIR": "01",
    "HIMACHAL PRADESH": "02",
    "PUNJAB": "03",
    "CHANDIGARH": "04",
    "UTTARAKHAND": "05",
    "HARYANA": "06",
    "DELHI": "07",
    "RAJASTHAN": "08",
    "UTTAR PRADESH": "09",
    "BIHAR": "10",
    "SIKKIM": "11",
    "ARUNACHAL PRADESH": "12",
    "NAGALAND": "13",
    "MANIPUR": "14",
    "MIZORAM": "15",
    "TRIPURA": "16",
    "MEGHALAYA": "17",
    "ASSAM": "18",
    "WEST BENGAL": "19",
    "JHARKHAND": "20",
    "ODISHA": "21",
    "CHHATTISGARH": "22",
    "MADHYA PRADESH": "23",
    "GUJARAT": "24",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": "26",
    "MAHARASHTRA": "27",
    "KARNATAKA": "29",
    "GOA": "30",
    "LAKSHADWEEP": "31",
    "KERALA": "32",
    "TAMIL NADU": "33",
    "PUDUCHERRY": "34",
    "ANDAMAN AND NICOBAR ISLANDS": "35",
    "TELANGANA": "36",
    "ANDHRA PRADESH": "37",
    "LADAKH": "38",
}


def get_state_code(state_name: str) -> str:
    if not state_name:
        return "--"
    return (STATE_CODES[state_name.upper().strip()] if state_name.upper().strip() in STATE_CODES else "--")


async def generate_invoice_pdf(
    order: PopulatedOrderResponse,
    payment: Payment,
    seller_info: SellerInvoiceInfo,
) -> BytesIO:
    """
    Generate PDF Invoice for an order
    Returns: BytesIO buffer containing PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)

    # Container for the 'Flowable' objects
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#000000"),
        alignment=TA_CENTER,
        spaceAfter=30,
    )

    # Title
    elements.append(Paragraph("TAX INVOICE", title_style))
    elements.append(Spacer(1, 20))

    # Seller and Buyer Information
    seller_lines = ["<b>From:</b>", seller_info.name]
    if seller_info.company_name:
        seller_lines.append(seller_info.company_name)
    if seller_info.gstin:
        seller_lines.append(f"GSTIN: {seller_info.gstin}")

    seller_addr = seller_info.address
    if seller_addr.street:
        seller_lines.append(seller_addr.street)
        if seller_addr.city and seller_addr.state:
            seller_lines.append(f"{seller_addr.city}, {seller_addr.state} (Code: {get_state_code(seller_addr.state)})")
        if seller_addr.pincode:
            seller_lines.append(f"PIN: {seller_addr.pincode}")

    buyer = order.user
    buyer_lines = ["<b>To:</b>", (buyer.name if buyer and buyer.name else "N/A")]
    if buyer and buyer.company_name:
        buyer_lines.append(buyer.company_name)

    shipping_address = order.shipping_address or order.address
    if shipping_address:
        if shipping_address.street:
            buyer_lines.append(shipping_address.street)
        if shipping_address.city and shipping_address.state:
            buyer_lines.append(f"{shipping_address.city}, {shipping_address.state} (Code: {get_state_code(shipping_address.state)})")
        if shipping_address.pincode:
            buyer_lines.append(f"PIN: {shipping_address.pincode}")

    # Create two-column table for seller/buyer info
    seller_text = "<br/>".join(seller_lines)
    buyer_text = "<br/>".join(buyer_lines)

    info_table = Table(
        [[Paragraph(seller_text, styles["Normal"]), Paragraph(buyer_text, styles["Normal"])]],
        colWidths=[100 * mm, 100 * mm],
    )

    info_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Invoice Details
    invoice_date = order.created_at or datetime.now(timezone.utc)
    invoice_number = order.order_number or f"ORD-{order.id}"
    payment_method = order.payment_method.upper() if order.payment_method else "N/A"
    place_of_supply = shipping_address.state.upper() if shipping_address and shipping_address.state else "N/A"

    invoice_details = [
        ["Invoice Number:", invoice_number],
        ["Invoice Date:", invoice_date.strftime("%d/%m/%Y")],
        ["Order Date:", invoice_date.strftime("%d/%m/%Y")],
        ["Payment Method:", payment_method],
        ["Place of Supply:", place_of_supply],
    ]

    details_table = Table(invoice_details, colWidths=[60 * mm, 140 * mm])
    details_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]
        )
    )

    elements.append(details_table)
    elements.append(Spacer(1, 20))

    # Items Table Header
    items_data = [
        ["S.No.", "Item Description", "HSN/SAC", "Qty", "Unit Price", "Taxable", "GST %", "GST Amount", "Total"]
    ]

    # Items
    # Determine if Intra-state (CGST/SGST) or Inter-state (IGST)
    seller_state = (seller_addr.state.upper().strip()) if (seller_addr and seller_addr.state) else ""
    buyer_state = (shipping_address.state.upper().strip()) if (shipping_address and shipping_address.state) else ""
    is_igst = seller_state != buyer_state and seller_state != "" and buyer_state != ""

    total_taxable = 0.0
    total_gst = 0.0

    for idx, item in enumerate(order.items or [], 1):
        product = item.product
        num_units = item.quantity or 0
        single_unit_price = item.price or 0.0
        gst_percent = item.tax_rate or 0.0
        item_total = single_unit_price * num_units

        item_tax_total = item.tax_amount or 0.0
        if item_tax_total == 0.0 and gst_percent > 0:
            taxable_value = item_total / (1 + gst_percent / 100)
            item_tax_total = item_total - taxable_value
        else:
            taxable_value = item_total - item_tax_total

        total_taxable += taxable_value
        total_gst += item_tax_total

        prod_name = product.name if product and product.name else "Item"
        hsn = product.hsn_code if product and product.hsn_code else "-"
        desc = f"{prod_name} (Ordered: {num_units})"

        items_data.append(
            [
                str(idx),
                desc,
                hsn,
                str(num_units),
                f"₹{single_unit_price:.2f}",
                f"₹{taxable_value:.2f}",
                f"{gst_percent:.0f}%",
                f"₹{item_tax_total:.2f}",
                f"₹{item_total:.2f}",
            ]
        )

    items_table = Table(items_data, colWidths=[30 * mm, 80 * mm, 50 * mm, 30 * mm, 40 * mm, 50 * mm, 40 * mm, 50 * mm])
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # Totals
    totals_data = [
        ["Subtotal (Taxable Value):", f"₹{total_taxable:.2f}"],
    ]

    if is_igst:
        totals_data.append(["IGST:", f"₹{total_gst:.2f}"])
    else:
        totals_data.append(["CGST:", f"₹{(total_gst / 2):.2f}"])
        totals_data.append(["SGST:", f"₹{(total_gst / 2):.2f}"])

    totals_data.append(["Total GST:", f"₹{total_gst:.2f}"])

    discount_val = order.discount or 0.0
    if discount_val > 0:
        totals_data.append(["Coupon Discount:", f"-₹{discount_val:.2f}"])

    shipping_val = order.shipping_charge or 0.0
    if shipping_val > 0:
        totals_data.append(["Delivery Charge:", f"₹{shipping_val:.2f}"])

    total_val = order.total or 0.0
    totals_data.append(["<b>Grand Total:</b>", f"<b>₹{int(total_val)}</b>"])

    totals_table = Table(totals_data, colWidths=[140 * mm, 60 * mm])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 12),
                ("FONTSIZE", (0, 0), (0, -2), 10),
            ]
        )
    )

    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # Payment Information
    paid_val = payment.amount_paid if payment.amount_paid is not None else total_val
    rem_val = payment.amount_remaining if payment.amount_remaining is not None else 0.0

    payment_info = [
        ["Payment Information:"],
        [f"Amount Paid: ₹{paid_val:.2f}"],
        [f"Amount Remaining: ₹{rem_val:.2f}"],
    ]

    payment_table = Table(payment_info)
    payment_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]
        )
    )

    elements.append(payment_table)

    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName="Helvetica-Oblique",
    )
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("This is a computer-generated invoice and does not require a signature.", footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


async def save_invoice_pdf(pdf_buffer: BytesIO, order_id: str) -> str:
    """
    Save invoice PDF to the private data directory (not the public uploads mount).
    Returns an opaque path that is served only through the authenticated
    GET /api/orders/{id}/invoice endpoint.
    """
    from app.utils.file_storage import DATA_DIR
    from app.config.settings import settings

    env = settings.environment.lower()
    if env == "production":
        env_folder = "SJ_PROD"
    elif env == "uat":
        env_folder = "SJ_UAT"
    else:
        env_folder = "SJ_LOCAL"

    # Store in DATA_DIR (private), NOT in uploads/ (public static mount).
    invoices_dir = Path(DATA_DIR) / "invoices" / env_folder
    invoices_dir.mkdir(parents=True, exist_ok=True)

    filename = f"invoice-{order_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}.pdf"
    file_path = invoices_dir / filename

    with open(file_path, "wb") as f:
        f.write(pdf_buffer.getvalue())

    # Return an internal path that is resolved by the download endpoint,
    # not a /uploads/ URL that would expose the file publicly.
    return f"invoices/{env_folder}/{filename}"
