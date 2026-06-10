#!/usr/bin/env python3
"""Add test sales data for profits display"""
import mysql.connector
from config import Config

def add_test_data():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
            database=Config.MYSQL_DATABASE
        )
        cursor = conn.cursor()
        
        # Add test sales
        sales_data = [
            ("2026-06-08", 2, "Nairobi Branch", 5000.00, 250.00),
            ("2026-06-08", 2, "Nairobi Branch", 7500.00, 375.00),
            ("2026-06-09", 2, "Nairobi Branch", 3500.00, 175.00),
        ]
        
        for sale in sales_data:
            cursor.execute(
                "INSERT INTO sales (sale_date, branch_id, branch_name, total_amount, total_sales_commission) VALUES (%s, %s, %s, %s, %s)",
                sale
            )
        
        conn.commit()
        
        # Get sale IDs
        cursor.execute("SELECT id FROM sales ORDER BY id DESC LIMIT 3")
        sale_ids = [row[0] for row in cursor.fetchall()]
        sale_ids.reverse()
        
        # Add sale items
        sale_items = [
            (sale_ids[0], 1, "Router X1", 2, 2500.00, 5000.00, 250.00),
            (sale_ids[1], 2, "Network Switch", 1, 4500.00, 4500.00, 225.00),
            (sale_ids[1], 3, "Ethernet Cable (10m)", 5, 350.00, 1750.00, 100.00),
            (sale_ids[2], 4, "WiFi Extender", 2, 1800.00, 3600.00, 160.00),
        ]
        
        for item in sale_items:
            cursor.execute(
                "INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price, commission) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                item
            )
        
        conn.commit()
        
        # Add expenses
        expenses = [
            (2, 500.00, "Rent for storage", "expense"),
            (2, 300.00, "Fuel", "expense"),
        ]
        
        for expense in expenses:
            cursor.execute(
                "INSERT INTO expenses (branch_id, amount, reason, type) VALUES (%s, %s, %s, %s)",
                expense
            )
        
        conn.commit()
        
        print("✅ Test sales data added successfully!")
        print("   - 3 sales records created")
        print("   - 4 sale items created")
        print("   - 2 expenses created")
        print("\nYour profits page should now show:")
        print("   - Total Revenue: Ksh 16,000.00")
        print("   - Gross Profit: will be calculated based on cost prices")
        print("   - Sales Commission: Ksh 800.00")
        print("   - Total Expenses: Ksh 800.00")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_test_data()
