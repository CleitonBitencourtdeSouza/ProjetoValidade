from database import add_product, add_batch, init_db


def seed_data():
    init_db()

    products = [
        ("7891234567890", "Milk 1L", "Dairy", 3.50),
        ("7891234567891", "Bread", "Bakery", 2.20),
        ("7891234567892", "Orange Juice", "Beverages", 4.00),
    ]

    for barcode, description, category, price in products:
        add_product(barcode, description, category, price)

    batches = [
        ("12345678901234567890123456789012345678901234", "Supplier A", "2026-10-15", "7891234567890", 20, "LOT-001", "2026-11-08"),
        ("12345678901234567890123456789012345678901234", "Supplier B", "2026-10-18", "7891234567891", 15, "LOT-010", "2026-11-18"),
        ("12345678901234567890123456789012345678901234", "Supplier C", "2026-10-20", "7891234567892", 12, "LOT-021", "2026-12-02"),
    ]

    for invoice_key, supplier, entry_date, barcode, quantity, batch_number, expiry_date in batches:
        try:
            add_batch(invoice_key, supplier, entry_date, barcode, quantity, batch_number, expiry_date)
        except ValueError:
            pass


if __name__ == "__main__":
    seed_data()
    print("Seed data loaded successfully.")
