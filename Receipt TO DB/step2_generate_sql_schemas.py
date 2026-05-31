"""
Receipt Database Schema Generator
Generates SQL scripts for SQL Server, MySQL, SQLite, and MongoDB
Based on the optimized JSON schema from generate_receipt_prompts.py
"""

import json
import os
from datetime import datetime

# Load the optimized schema
with open('optimized_json_schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

OUTPUT_DIR = "sql_schemas"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def to_snake_case(name):
    """Convert camelCase to snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

# ============================================================
# SQL Server Schema
# ============================================================

def generate_sql_server():
    sql = """-- ============================================
-- SQL Server Schema for Receipt Data
-- Generated: {date}
-- ============================================

-- Drop tables if exist (in correct order due to foreign keys)
IF OBJECT_ID('receipt_tax_breakdown', 'U') IS NOT NULL DROP TABLE receipt_tax_breakdown;
IF OBJECT_ID('receipt_items', 'U') IS NOT NULL DROP TABLE receipt_items;
IF OBJECT_ID('receipts', 'U') IS NOT NULL DROP TABLE receipts;

-- Main receipts table
CREATE TABLE receipts (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    receipt_number NVARCHAR(100) NOT NULL UNIQUE,
    merchant_name NVARCHAR(255),
    merchant_address NVARCHAR(500),
    merchant_phone NVARCHAR(50),
    merchant_tax_id NVARCHAR(50),
    transaction_date DATE,
    transaction_time TIME,
    clerk NVARCHAR(100),
    subtotal DECIMAL(12, 2),
    tax_amount DECIMAL(12, 2),
    total_amount DECIMAL(12, 2),
    payment_method NVARCHAR(50),
    amount_tendered DECIMAL(12, 2),
    change_due DECIMAL(12, 2),
    created_at DATETIME DEFAULT GETDATE()
);

-- Receipt items table (one-to-many)
CREATE TABLE receipt_items (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    receipt_id BIGINT NOT NULL,
    description NVARCHAR(500),
    quantity DECIMAL(10, 2),
    unit_price DECIMAL(12, 2),
    line_total DECIMAL(12, 2),
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

-- Tax breakdown table (one-to-many)
CREATE TABLE receipt_tax_breakdown (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    receipt_id BIGINT NOT NULL,
    tax_type NVARCHAR(50),
    tax_rate DECIMAL(6, 4),
    tax_amount DECIMAL(12, 2),
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

-- Create indexes for common queries
CREATE INDEX idx_receipts_date ON receipts(transaction_date);
CREATE INDEX idx_receipts_merchant ON receipts(merchant_name);
CREATE INDEX idx_receipts_number ON receipts(receipt_number);
CREATE INDEX idx_items_receipt ON receipt_items(receipt_id);
CREATE INDEX idx_tax_receipt ON receipt_tax_breakdown(receipt_id);

PRINT 'SQL Server schema created successfully.';
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return sql

# ============================================================
# MySQL Schema
# ============================================================

def generate_mysql():
    sql = """-- ============================================
-- MySQL Schema for Receipt Data
-- Generated: {date}
-- ============================================

-- Drop tables if exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS receipt_tax_breakdown;
DROP TABLE IF EXISTS receipt_items;
DROP TABLE IF EXISTS receipts;

-- Main receipts table
CREATE TABLE receipts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    receipt_number VARCHAR(100) NOT NULL UNIQUE,
    merchant_name VARCHAR(255),
    merchant_address VARCHAR(500),
    merchant_phone VARCHAR(50),
    merchant_tax_id VARCHAR(50),
    transaction_date DATE,
    transaction_time TIME,
    clerk VARCHAR(100),
    subtotal DECIMAL(12, 2),
    tax_amount DECIMAL(12, 2),
    total_amount DECIMAL(12, 2),
    payment_method VARCHAR(50),
    amount_tendered DECIMAL(12, 2),
    change_due DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Receipt items table (one-to-many)
CREATE TABLE receipt_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    receipt_id BIGINT NOT NULL,
    description VARCHAR(500),
    quantity DECIMAL(10, 2),
    unit_price DECIMAL(12, 2),
    line_total DECIMAL(12, 2),
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tax breakdown table (one-to-many)
CREATE TABLE receipt_tax_breakdown (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    receipt_id BIGINT NOT NULL,
    tax_type VARCHAR(50),
    tax_rate DECIMAL(6, 4),
    tax_amount DECIMAL(12, 2),
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create indexes for common queries
CREATE INDEX idx_receipts_date ON receipts(transaction_date);
CREATE INDEX idx_receipts_merchant ON receipts(merchant_name);
CREATE INDEX idx_receipts_number ON receipts(receipt_number);
CREATE INDEX idx_items_receipt ON receipt_items(receipt_id);
CREATE INDEX idx_tax_receipt ON receipt_tax_breakdown(receipt_id);

SELECT 'MySQL schema created successfully.' AS status;
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return sql

# ============================================================
# SQLite Schema
# ============================================================

def generate_sqlite():
    sql = """-- ============================================
-- SQLite Schema for Receipt Data
-- Generated: {date}
-- ============================================

-- Drop tables if exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS receipt_tax_breakdown;
DROP TABLE IF EXISTS receipt_items;
DROP TABLE IF EXISTS receipts;

-- Main receipts table
CREATE TABLE receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_number TEXT NOT NULL UNIQUE,
    merchant_name TEXT,
    merchant_address TEXT,
    merchant_phone TEXT,
    merchant_tax_id TEXT,
    transaction_date TEXT,
    transaction_time TEXT,
    clerk TEXT,
    subtotal REAL,
    tax_amount REAL,
    total_amount REAL,
    payment_method TEXT,
    amount_tendered REAL,
    change_due REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Receipt items table (one-to-many)
CREATE TABLE receipt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    description TEXT,
    quantity REAL,
    unit_price REAL,
    line_total REAL,
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

-- Tax breakdown table (one-to-many)
CREATE TABLE receipt_tax_breakdown (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    tax_type TEXT,
    tax_rate REAL,
    tax_amount REAL,
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

-- Create indexes for common queries
CREATE INDEX idx_receipts_date ON receipts(transaction_date);
CREATE INDEX idx_receipts_merchant ON receipts(merchant_name);
CREATE INDEX idx_receipts_number ON receipts(receipt_number);
CREATE INDEX idx_items_receipt ON receipt_items(receipt_id);
CREATE INDEX idx_tax_receipt ON receipt_tax_breakdown(receipt_id);

SELECT 'SQLite schema created successfully.' AS status;
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return sql

# ============================================================
# MongoDB Schema
# ============================================================

def generate_mongodb():
    schema = {
        "receipts": {
            "_id": "ObjectId",
            "receipt_number": "string (unique)",
            "merchant": {
                "name": "string",
                "address": "string",
                "phone": "string",
                "tax_id": "string"
            },
            "transaction": {
                "date": "ISODate (YYYY-MM-DD)",
                "time": "string (HH:MM)",
                "receipt_number": "string",
                "clerk": "string"
            },
            "items": [
                {
                    "description": "string",
                    "quantity": "number",
                    "unit_price": "number",
                    "line_total": "number"
                }
            ],
            "summary": {
                "subtotal": "number",
                "tax_amount": "number",
                "total_amount": "number",
                "tax_breakdown": [
                    {
                        "type": "string",
                        "rate": "number",
                        "amount": "number"
                    }
                ]
            },
            "payment": {
                "method": "string",
                "amount_tendered": "number",
                "change_due": "number"
            },
            "created_at": "ISODate"
        }
    }

    js = """// ============================================
// MongoDB Schema for Receipt Data
// Generated: {date}
// ============================================

// Create receipts collection with validation
db.createCollection("receipts", {{
    validator: {{
        $jsonSchema: {{
            bsonType: "object",
            required: ["receipt_number"],
            properties: {{
                receipt_number: {{
                    bsonType: "string",
                    description: "unique receipt identifier"
                }},
                merchant: {{
                    bsonType: "object",
                    properties: {{
                        name: {{ bsonType: "string" }},
                        address: {{ bsonType: "string" }},
                        phone: {{ bsonType: "string" }},
                        tax_id: {{ bsonType: "string" }}
                    }}
                }},
                transaction: {{
                    bsonType: "object",
                    properties: {{
                        date: {{ bsonType: "date" }},
                        time: {{ bsonType: "string" }},
                        receipt_number: {{ bsonType: "string" }},
                        clerk: {{ bsonType: "string" }}
                    }}
                }},
                items: {{
                    bsonType: "array",
                    items: {{
                        bsonType: "object",
                        properties: {{
                            description: {{ bsonType: "string" }},
                            quantity: {{ bsonType: "number" }},
                            unit_price: {{ bsonType: "number" }},
                            line_total: {{ bsonType: "number" }}
                        }}
                    }}
                }},
                summary: {{
                    bsonType: "object",
                    properties: {{
                        subtotal: {{ bsonType: "number" }},
                        tax_amount: {{ bsonType: "number" }},
                        total_amount: {{ bsonType: "number" }},
                        tax_breakdown: {{
                            bsonType: "array",
                            items: {{
                                bsonType: "object",
                                properties: {{
                                    type: {{ bsonType: "string" }},
                                    rate: {{ bsonType: "number" }},
                                    amount: {{ bsonType: "number" }}
                                }}
                            }}
                        }}
                    }}
                }},
                payment: {{
                    bsonType: "object",
                    properties: {{
                        method: {{ bsonType: "string" }},
                        amount_tendered: {{ bsonType: "number" }},
                        change_due: {{ bsonType: "number" }}
                    }}
                }},
                created_at: {{ bsonType: "date" }}
            }}
        }}
    }}
}});

// Create indexes for common queries
db.receipts.createIndex({{ "receipt_number": 1 }}, {{ unique: true }});
db.receipts.createIndex({{ "transaction.date": 1 }});
db.receipts.createIndex({{ "merchant.name": 1 }});

// Example insert
db.receipts.insertOne({{
    receipt_number: "RCP-001",
    merchant: {{
        name: "Store Name",
        address: "123 Main St, City, ST 12345",
        phone: "(555) 123-4567",
        tax_id: "12-3456789"
    }},
    transaction: {{
        date: new Date("2024-01-15"),
        time: "14:30",
        receipt_number: "RCP-001",
        clerk: "John Doe"
    }},
    items: [
        {{
            description: "Item 1",
            quantity: 2,
            unit_price: 10.00,
            line_total: 20.00
        }}
    ],
    summary: {{
        subtotal: 20.00,
        tax_amount: 1.60,
        total_amount: 21.60,
        tax_breakdown: [
            {{ type: "sales_tax", rate: 0.08, amount: 1.60 }}
        ]
    }},
    payment: {{
        method: "CASH",
        amount_tendered: 25.00,
        change_due: 3.40
    }},
    created_at: new Date()
}});

print('MongoDB schema created successfully.');
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return js

# ============================================================
# Generate All Schemas
# ============================================================

print("=" * 60)
print("Generating SQL Schemas for All Database Platforms")
print("=" * 60)

# Save SQL Server schema
sql_server_file = os.path.join(OUTPUT_DIR, "sqlserver_schema.sql")
with open(sql_server_file, 'w', encoding='utf-8') as f:
    f.write(generate_sql_server())
print(f"[OK] SQL Server schema -> {sql_server_file}")

# Save MySQL schema
mysql_file = os.path.join(OUTPUT_DIR, "mysql_schema.sql")
with open(mysql_file, 'w', encoding='utf-8') as f:
    f.write(generate_mysql())
print(f"[OK] MySQL schema -> {mysql_file}")

# Save SQLite schema
sqlite_file = os.path.join(OUTPUT_DIR, "sqlite_schema.sql")
with open(sqlite_file, 'w', encoding='utf-8') as f:
    f.write(generate_sqlite())
print(f"[OK] SQLite schema -> {sqlite_file}")

# Save MongoDB schema
mongodb_file = os.path.join(OUTPUT_DIR, "mongodb_schema.js")
with open(mongodb_file, 'w', encoding='utf-8') as f:
    f.write(generate_mongodb())
print(f"[OK] MongoDB schema -> {mongodb_file}")

print("\n" + "=" * 60)
print("All SQL schemas generated successfully!")
print("=" * 60)
print(f"\nFiles in {OUTPUT_DIR}/:")
for f in os.listdir(OUTPUT_DIR):
    print(f"  - {f}")