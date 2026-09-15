"""
Invoice PDF Generator for Orders
"""

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


async def generate_invoice_pdf(order: Dict, payment: Dict, seller_info: Dict) -> BytesIO:
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
    seller_lines = ["<b>From:</b>", (seller_info["name"] if "name" in seller_info else "Stationery Junction")]
    if (seller_info["companyName"] if "companyName" in seller_info else None):
        seller_lines.append(seller_info["companyName"])
    if (seller_info["gstin"] if "gstin" in seller_info else None):
        seller_lines.append(f"GSTIN: {seller_info['gstin']}")

    seller_address = (seller_info["address"] if "address" in seller_info else {})
    if (seller_address["street"] if "street" in seller_address else None):
        seller_lines.append(seller_address["street"])
    if (seller_address["city"] if "city" in seller_address else None) and (seller_address["state"] if "state" in seller_address else None):
        state = seller_address["state"]
        seller_lines.append(f"{seller_address['city']}, {state} (Code: {get_state_code(state)})")
    if (seller_address["pincode"] if "pincode" in seller_address else None):
        seller_lines.append(f"PIN: {seller_address['pincode']}")

    buyer = (order["user"] if "user" in order else {})
    buyer_lines = ["<b>To:</b>", (buyer["name"] if "name" in buyer else "N/A")]
    if (buyer["companyName"] if "companyName" in buyer else None):
        buyer_lines.append(buyer["companyName"])
    if (buyer["gstin"] if "gstin" in buyer else None):
        buyer_lines.append(f"GSTIN: {buyer['gstin']}")

    shipping_address = (order["shippingAddress"] if "shippingAddress" in order else {})
    if (shipping_address["street"] if "street" in shipping_address else None):
        buyer_lines.append(shipping_address["street"])
    if (shipping_address["city"] if "city" in shipping_address else None) and (shipping_address["state"] if "state" in shipping_address else None):
        state = shipping_address["state"]
        buyer_lines.append(f"{shipping_address['city']}, {state} (Code: {get_state_code(state)})")
    if (shipping_address["pincode"] if "pincode" in shipping_address else None) or (shipping_address["zipCode"] if "zipCode" in shipping_address else None):
        buyer_lines.append(f"PIN: {(shipping_address['pincode'] if 'pincode' in shipping_address else None) or (shipping_address['zipCode'] if 'zipCode' in shipping_address else None)}")

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
    invoice_date = datetime.fromisoformat((order["createdAt"] if "createdAt" in order else datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00"))
    invoice_details = [
        ["Invoice Number:", (order["orderNumber"] if "orderNumber" in order else (order["_id"] if "_id" in order else "N/A"))],
        ["Invoice Date:", invoice_date.strftime("%d/%m/%Y")],
        ["Order Date:", invoice_date.strftime("%d/%m/%Y")],
        ["Payment Method:", ((order["paymentMethod"] if "paymentMethod" in order else "N/A")).upper()],
        ["Place of Supply:", (shipping_address["state"] if "state" in shipping_address else "N/A").upper()],
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
    seller_state = ((seller_info["address"] if "address" in seller_info else {})["state"] if "state" in (seller_info["address"] if "address" in seller_info else {}) else None or "").upper().strip()
    buyer_state = ((order["shippingAddress"] if "shippingAddress" in order else {})["state"] if "state" in (seller_info["address"] if "address" in seller_info else {}) else None or "").upper().strip()
    is_igst = seller_state != buyer_state and seller_state != "" and buyer_state != ""

    total_taxable = 0.0
    total_gst = 0.0

    for idx, item in enumerate((order["items"] if "items" in order else []), 1):
        product = (item["product"] if "product" in item else {})

        # Read new single unit fields with fallbacks to old fields
        single_unit_price = (item["singleUnitPrice"] if "singleUnitPrice" in item else (item["price"] if "price" in item else 0))
        num_units = (item["numberOfSingleUnits"] if "numberOfSingleUnits" in item else (item["quantity"] if "quantity" in item else 0))
        gst_percent = (item["gst"] if "gst" in item else 0)

        item_total = (item["subtotal"] if "subtotal" in item else single_unit_price * num_units)
        taxable_value = (item["taxableValue"] if "taxableValue" in item else 0)
        if not taxable_value:
            taxable_value = item_total / (1 + gst_percent / 100) if gst_percent > 0 else item_total

        cgst = (item["cgst"] if "cgst" in item else 0)
        sgst = (item["sgst"] if "sgst" in item else 0)
        item_tax_total = cgst + sgst
        if item_tax_total == 0 and gst_percent > 0:
            item_tax_total = item_total - taxable_value

        total_taxable += taxable_value
        total_gst += item_tax_total

        # Format item description to show original quantity
        qty_str = f"{(item['quantity'] if 'quantity' in item else 0)}"
        if (item["sellAsCase"] if "sellAsCase" in item else None):
            qty_str += " Case(s)"

        desc = f"{(product['name'] if 'name' in product else 'N/A')} (Ordered: {qty_str})"

        items_data.append(
            [
                str(idx),
                desc,
                (product["hsnCode"] if "hsnCode" in product else "-"),
                str(num_units),
                f"₹{single_unit_price:.2f}",
                f"₹{taxable_value:.2f}",
                f"{gst_percent}%",
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

    if (order["discount"] if "discount" in order else 0) > 0:
        totals_data.append(["Coupon Discount:", f"-₹{order['discount']:.2f}"])

    if (order["shipping"] if "shipping" in order else 0) > 0:
        totals_data.append(["Delivery Charge:", f"₹{order['shipping']:.2f}"])

    totals_data.append(["<b>Grand Total:</b>", f"<b>₹{int((order['total'] if 'total' in order else 0))}</b>"])

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
    payment_info = [
        ["Payment Information:"],
        [f"Amount Paid: ₹{((payment['amountPaid'] if 'amountPaid' in payment else None) or 0):.2f}"],
        [f"Amount Remaining: ₹{((payment['amountRemaining'] if 'amountRemaining' in payment else None) or 0):.2f}"],
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
    Save invoice PDF to file system
    Returns: File path relative to uploads directory
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

    invoices_dir = Path(DATA_DIR).parent / "uploads" / env_folder / "invoices"
    invoices_dir.mkdir(parents=True, exist_ok=True)

    filename = f"invoice-{order_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}.pdf"
    file_path = invoices_dir / filename

    with open(file_path, "wb") as f:
        f.write(pdf_buffer.getvalue())

    return f"/uploads/{env_folder}/invoices/{filename}"
