# Inventory Management System (with Open Food Facts Integration)

Welcome to the **Inventory Management System**, a lightweight, local-first inventory tracker featuring a Flask REST API, an interactive Command-Line Interface (CLI), and external product data auto-population using the Open Food Facts API. 

This project also features a robust suite of unit tests powered by `pytest` to ensure structural integrity across the system.

---

## Features

* **RESTful Flask API**: Complete CRUD operations (`GET`, `POST`, `PATCH`, `DELETE`) with an in-memory database fallback.
* **Smart Barcode Lookup**: Automatically retrieves product names from the external **Open Food Facts API** if a barcode is supplied without a name.
* **Interactive CLI Tool**: User-friendly menu to view all inventory, search for explicit items, add stock, update values, and delete entries.
* **Complete Test Coverage**: Unit tests covering API endpoints, external network request mocking, and CLI logic.

---

##  Project Structure

```text
├── App/
│   └── main.py          # Flask API backend & external integration
├── cli_tool.py          # Interactive command-line tool
├── test_app.py          # Pytest file containing API, External API, and CLI unit tests
├── requirements.txt     # Python package dependencies
└── README.md            # Project documentation
