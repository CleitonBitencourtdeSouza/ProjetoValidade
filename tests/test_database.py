import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import database
from database import (
    add_batch,
    add_product,
    get_loss_report,
    get_products,
    get_products_for_alerts,
    get_batches_for_dashboard,
    init_db,
    update_batch_status,
    validate_nf_key,
    get_alert_level,
)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        temp_db = Path(tempfile.mkdtemp()) / "test_expiry_tracker.db"
        database.DB_PATH = str(temp_db)
        init_db()

    def test_validate_nf_key_accepts_44_numeric_digits(self):
        self.assertTrue(validate_nf_key("12345678901234567890123456789012345678901234"))

    def test_validate_nf_key_rejects_invalid_values(self):
        self.assertFalse(validate_nf_key("123"))
        self.assertFalse(validate_nf_key("abc12345678901234567890123456789012345678901234"))

    def test_get_alert_level_for_expiry_dates(self):
        today = date.today()
        self.assertEqual(get_alert_level(today - timedelta(days=1)), "expired")
        self.assertEqual(get_alert_level(today + timedelta(days=3)), "critical")
        self.assertEqual(get_alert_level(today + timedelta(days=10)), "warning")
        self.assertEqual(get_alert_level(today + timedelta(days=20)), "attention")

    def test_product_registration_keeps_expiry_date_and_alert_visibility(self):
        self.assertTrue(
            add_product(
                "1111111111111",
                "Produto de teste",
                "Bebidas",
                18.90,
                "2035-12-31",
            )
        )

        products = get_products()
        self.assertTrue(
            any(
                product["barcode"] == "1111111111111"
                and product["expiry_date"] == "2035-12-31"
                for product in products
            )
        )

        alerts = get_products_for_alerts()
        self.assertTrue(
            any(alert["barcode"] == "1111111111111" for alert in alerts)
        )

    def test_discarded_batch_disappears_from_alerts_and_appears_in_loss_report(self):
        self.assertTrue(
            add_product(
                "2222222222222",
                "Produto descartado",
                "Bebidas",
                10.00,
                "2035-12-31",
            )
        )

        add_batch(
            "12345678901234567890123456789012345678901234",
            "Fornecedor X",
            "2026-11-01",
            "2222222222222",
            5,
            "LOT-999",
            "2026-11-10",
        )

        batches = get_batches_for_dashboard()
        self.assertTrue(any(batch["batch_number"] == "LOT-999" for batch in batches))

        batch = get_batches_for_dashboard()[0] if get_batches_for_dashboard() else None
        if batch is not None:
            update_batch_status(batch["id"], "discarded")

        remaining = get_batches_for_dashboard()
        self.assertFalse(any(item["batch_number"] == "LOT-999" for item in remaining))

        report = get_loss_report("2026-11-01", "2026-11-30")
        self.assertTrue(any(item["category"] == "Bebidas" for item in report))


if __name__ == "__main__":
    unittest.main()
