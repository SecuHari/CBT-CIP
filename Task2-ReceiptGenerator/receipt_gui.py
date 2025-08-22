import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import datetime
import os

# -----------------------------
# PDF Receipt Generator
# -----------------------------
def generate_receipt():
    name = entry_name.get()
    amount = entry_amount.get()
    payment_mode = payment_mode_var.get()
    receipt_no = entry_receipt.get()

    if not name or not amount or not receipt_no:
        messagebox.showerror("Error", "All fields are required!")
        return

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number")
        return

    today = datetime.date.today().strftime("%d-%m-%Y")

    # PDF file name
    filename = f"receipt_{receipt_no}.pdf"

    # Create PDF
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height-80, "PAYMENT RECEIPT")

    c.setFont("Helvetica", 14)
    c.drawString(50, height-150, f"Receipt No: {receipt_no}")
    c.drawString(50, height-180, f"Date: {today}")
    c.drawString(50, height-220, f"Received From: {name}")
    c.drawString(50, height-260, f"Amount: ₹ {amount:.2f}")
    c.drawString(50, height-300, f"Payment Mode: {payment_mode}")

    c.line(50, height-320, width-50, height-320)
    c.setFont("Helvetica-Oblique", 12)
    c.drawString(50, height-350, "This is a computer-generated receipt.")

    c.save()

    messagebox.showinfo("Success", f"✅ Receipt generated successfully:\n{filename}")
    os.startfile(filename)  # Auto open after generation (Windows only)

# -----------------------------
# Tkinter GUI
# -----------------------------
root = tk.Tk()
root.title("Receipt Generator")
root.geometry("500x400")
root.resizable(False, False)

# Heading
heading = tk.Label(root, text="Receipt Generator", font=("Arial", 20, "bold"), fg="navy")
heading.pack(pady=10)

# Form Frame
frame = tk.Frame(root, padx=20, pady=20)
frame.pack(pady=10)

# Customer Name
tk.Label(frame, text="Customer Name:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=5)
entry_name = tk.Entry(frame, font=("Arial", 12), width=25)
entry_name.grid(row=0, column=1, pady=5)

# Amount
tk.Label(frame, text="Amount (₹):", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
entry_amount = tk.Entry(frame, font=("Arial", 12), width=25)
entry_amount.grid(row=1, column=1, pady=5)

# Payment Mode
tk.Label(frame, text="Payment Mode:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
payment_mode_var = tk.StringVar()
payment_dropdown = ttk.Combobox(frame, textvariable=payment_mode_var, font=("Arial", 12), width=23, state="readonly")
payment_dropdown["values"] = ("Cash", "UPI", "Card", "Bank Transfer", "Other")
payment_dropdown.current(0)
payment_dropdown.grid(row=2, column=1, pady=5)

# Receipt No
tk.Label(frame, text="Receipt No:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=5)
entry_receipt = tk.Entry(frame, font=("Arial", 12), width=25)
entry_receipt.grid(row=3, column=1, pady=5)

# Generate Button
btn_generate = tk.Button(root, text="Generate Receipt", font=("Arial", 14, "bold"), bg="navy", fg="white",
                         command=generate_receipt, padx=10, pady=5)
btn_generate.pack(pady=20)

# Run App
root.mainloop()
