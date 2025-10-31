"""
Data Processor Module

Transforms raw Amazon order data into Firefly III compatible CSV format.
Handles data cleaning, normalization, and CSV generation.
"""

import os
import csv
import re
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

from .data_extractor import OrderData
from .config import Config


class DataProcessor:
    """
    Processes and transforms order data for Firefly III import.

    Handles:
    - Data cleaning and normalization
    - Firefly III CSV schema mapping
    - Currency conversion and formatting
    - CSV file generation
    """

    # Firefly III CSV column mapping
    FIREFLY_CSV_HEADERS = [
        'date', 'amount', 'description', 'source_name', 'destination_name',
        'category_name', 'tags', 'notes', 'internal_reference', 'external_id',
        'reconciled', 'bill_name', 'bill_id', 'budget_name', 'budget_id'
    ]

    def __init__(self, config: Config):
        """
        Initialize the data processor.

        Args:
            config: Application configuration
        """
        self.config = config
        self.output_dir = config.get('output_dir', 'output')
        self.date_format = config.get('date_format', '%Y-%m-%d')

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def process_orders(self, orders: List[OrderData]) -> str:
        """
        Process order data and generate Firefly III CSV file.

        Args:
            orders: List of OrderData objects to process

        Returns:
            Path to generated CSV file
        """
        print(f"Processing {len(orders)} orders...")

        # Convert orders to Firefly III format
        firefly_data = []
        for order in orders:
            try:
                firefly_row = self._convert_to_firefly_format(order)
                if firefly_row:
                    firefly_data.append(firefly_row)
            except Exception as e:
                print(f"Error processing order {order.order_id}: {e}")
                continue

        if not firefly_data:
            raise ValueError("No valid orders to process")

        # Generate CSV file
        csv_path = self._generate_csv_file(firefly_data)

        print(f"Generated CSV file: {csv_path}")
        print(f"Processed {len(firefly_data)} orders successfully")

        return csv_path

    def _convert_to_firefly_format(self, order: OrderData) -> Dict[str, Any]:
        """
        Convert OrderData to Firefly III CSV format.

        Args:
            order: OrderData object to convert

        Returns:
            Dictionary with Firefly III CSV fields
        """
        # Parse and format date
        formatted_date = self._format_date(order.date)

        # Parse and format amount
        formatted_amount = self._format_amount(order.amount)

        # Create description
        description = self._create_description(order)

        return {
            'date': formatted_date,
            'amount': formatted_amount,
            'description': description,
            'source_name': 'Amazon',  # Source account (expense from Amazon)
            'destination_name': '',  # Destination account (leave empty for expenses)
            'category_name': 'Shopping',  # Default category
            'tags': 'amazon,online-shopping',
            'notes': f"Order ID: {order.order_id}",
            'internal_reference': order.order_id,
            'external_id': order.order_id,
            'reconciled': 'false',
            'bill_name': '',
            'bill_id': '',
            'budget_name': '',
            'budget_id': ''
        }

    def _format_date(self, date_str: str) -> str:
        """
        Parse and format date string to Firefly III format.

        Args:
            date_str: Raw date string from Amazon

        Returns:
            Formatted date string (YYYY-MM-DD)
        """
        if not date_str:
            return datetime.now().strftime(self.date_format)

        try:
            # Handle Italian month names
            italian_months = {
                'gen': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'mag': '05', 'giu': '06',
                'lug': '07', 'ago': '08', 'set': '09', 'ott': '10', 'nov': '11', 'dic': '12'
            }

            # Try Italian format: "15 gen 2024"
            match = re.search(r'(\d{1,2})\s+(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)\s+(\d{4})',
                            date_str, re.IGNORECASE)
            if match:
                day, month_name, year = match.groups()
                month = italian_months.get(month_name.lower(), '01')
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime(self.date_format)

            # Try ISO format: "2024-01-15"
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
            if match:
                year, month, day = match.groups()
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime(self.date_format)

            # Try US format: "01/15/2024"
            match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
            if match:
                month, day, year = match.groups()
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime(self.date_format)

            # If no pattern matches, return current date
            print(f"Could not parse date: {date_str}")
            return datetime.now().strftime(self.date_format)

        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            return datetime.now().strftime(self.date_format)

    def _format_amount(self, amount_str: str) -> str:
        """
        Parse and format amount string for Firefly III.

        Args:
            amount_str: Raw amount string from Amazon

        Returns:
            Formatted amount string (negative for expenses)
        """
        if not amount_str:
            return "-0.00"

        try:
            # Extract numeric value from EUR format
            match = re.search(r'[\d,]+\.?\d*', amount_str.replace('EUR', '').strip())
            if match:
                amount = match.group(0).replace(',', '')
                # Convert to float and make negative (expense)
                return f"-{float(amount):.2f}"

            return "-0.00"

        except Exception as e:
            print(f"Error parsing amount '{amount_str}': {e}")
            return "-0.00"

    def _create_description(self, order: OrderData) -> str:
        """
        Create a clean description for the transaction.

        Args:
            order: OrderData object

        Returns:
            Formatted description string
        """
        description = order.description or "Amazon Purchase"

        # Clean up description
        description = re.sub(r'\s+', ' ', description).strip()  # Remove extra whitespace
        description = description[:100]  # Limit length

        # Add order ID if not already in description
        if order.order_id and order.order_id not in description:
            description = f"{description} (Order: {order.order_id})"

        return description

    def _generate_csv_file(self, firefly_data: List[Dict[str, Any]]) -> str:
        """
        Generate CSV file from processed data.

        Args:
            firefly_data: List of dictionaries with Firefly III format data

        Returns:
            Path to generated CSV file
        """
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"amazon_orders_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)

        try:
            # Use pandas for reliable CSV generation
            df = pd.DataFrame(firefly_data)
            df.to_csv(filepath, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')

            return filepath

        except Exception as e:
            raise RuntimeError(f"Failed to generate CSV file: {e}")

    def validate_csv_for_firefly(self, csv_path: str) -> bool:
        """
        Validate that generated CSV meets Firefly III requirements.

        Args:
            csv_path: Path to CSV file to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            df = pd.read_csv(csv_path)

            # Check required columns
            required_columns = ['date', 'amount', 'description']
            for col in required_columns:
                if col not in df.columns:
                    print(f"Missing required column: {col}")
                    return False

            # Check for data
            if len(df) == 0:
                print("CSV file is empty")
                return False

            # Validate date format
            try:
                pd.to_datetime(df['date'], format=self.date_format)
            except Exception as e:
                print(f"Invalid date format in CSV: {e}")
                return False

            # Validate amount format
            try:
                df['amount'].astype(float)
            except Exception as e:
                print(f"Invalid amount format in CSV: {e}")
                return False

            print("CSV validation successful")
            return True

        except Exception as e:
            print(f"Error validating CSV: {e}")
            return False