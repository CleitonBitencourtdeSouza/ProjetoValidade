# Expiry Tracker

## Problem
Supermarkets lose money when products reach expiry without being identified early enough. This causes waste, reduced margins, and operational friction in the store.

## Solution
This project provides a simple system to register products, record supplier batches, view expiry alerts, and monitor discarded stock by category and period.

## Features
- Product registration with barcode, description, category, and cost price.
- Batch registration through an invoice access key.
- Validation of the 44-digit NF-e key.
- Expiry dashboard with different alert levels.
- Batch status updates such as sold, promoted, returned, or discarded.
- Loss report by category and period.

## Tech stack
- Python
- SQLite
- Streamlit

## How to run
1. Open a terminal in the project folder.
2. Install dependencies:
   python -m pip install -r requirements.txt
3. Start the app:
   streamlit run app.py
4. Access the browser at http://localhost:8501

## Demo data
Run the following command to insert sample products and batches:

python seed_data.py

## Next steps
- Automatic import of NF-e XML.
- Barcode reading via camera.
- Oracle migration.
- User login.

## Built with AI-assisted development (Claude Code)
