from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_receipt(customer_name, items, total_amount, receipt_no):
    # Receipt file name
    file_name = f"receipt_{receipt_no}.pdf"
    
    # Setup PDF
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 50, "Payment Receipt")

    # Receipt Info
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Receipt No: {receipt_no}")
    c.drawString(50, height - 120, f"Customer Name: {customer_name}")
    c.drawString(50, height - 140, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Items Table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 180, "Item")
    c.drawString(300, height - 180, "Price (₹)")

    y = height - 200
    c.setFont("Helvetica", 12)
    for item, price in items.items():
        c.drawString(50, y, item)
        c.drawString(300, y, str(price))
        y -= 20

    # Total
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y - 20, f"Total Amount: ₹{total_amount}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, "Thank you for your purchase!")
    c.drawString(50, 35, "This is a system-generated receipt.")

    # Save PDF
    c.save()
    print(f"✅ Receipt generated successfully: {file_name}")


# Example Usage
if __name__ == "__main__":
    customer = "Hareesh Kumar"
    purchased_items = {
        "Laptop Bag": 1500,
        "Mouse": 700,
        "USB Cable": 250
    }
    total = sum(purchased_items.values())
    receipt_number = 101

    generate_receipt(customer, purchased_items, total, receipt_number)
