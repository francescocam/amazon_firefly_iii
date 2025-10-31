"""
Data Extractor Module

Scrapes order information from Amazon order history pages.
Extracts transaction details including dates, amounts, descriptions, and merchant info.
"""

import re
import time
from datetime import datetime
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import Config


class OrderData:
    """
    Represents a single Amazon order with all relevant transaction data.
    """

    def __init__(self, order_id: str = "", date: str = "", amount: str = "",
                 description: str = "", merchant: str = "Amazon"):
        self.order_id = order_id
        self.date = date
        self.amount = amount
        self.description = description
        self.merchant = merchant

    def to_dict(self) -> Dict[str, str]:
        """Convert order data to dictionary format."""
        return {
            'order_id': self.order_id,
            'date': self.date,
            'amount': self.amount,
            'description': self.description,
            'merchant': self.merchant
        }

    def __str__(self) -> str:
        return f"Order {self.order_id}: {self.description} - {self.amount} on {self.date}"


class DataExtractor:
    """
    Extracts order data from Amazon order history pages.

    Handles:
    - Order element identification and parsing
    - Pagination through order history
    - Data validation and cleaning
    """

    def __init__(self, driver, config: Config):
        """
        Initialize the data extractor.

        Args:
            driver: Selenium WebDriver instance
            config: Application configuration
        """
        self.driver = driver
        self.config = config
        self.wait_timeout = config.get('element_wait_timeout', 15)

    def extract_orders_by_years(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[OrderData]:
        """
        Extract order data for a range of years.

        Args:
            start_year: Starting year (None for current year)
            end_year: Ending year (None for current year)

        Returns:
            List of OrderData objects
        """
        # Set defaults to current year if not specified
        current_year = datetime.now().year
        if start_year is None:
            start_year = current_year
        if end_year is None:
            end_year = current_year

        # Ensure start_year <= end_year
        if start_year > end_year:
            start_year, end_year = end_year, start_year

        print(f"Starting extraction for years {start_year} to {end_year}")
        all_orders = []

        for year in range(start_year, end_year + 1):
            print(f"Processing year {year}...")
            year_orders = self._extract_orders_for_year(year)
            all_orders.extend(year_orders)
            print(f"Found {len(year_orders)} orders for year {year}")

        print(f"Total orders extracted: {len(all_orders)}")
        return all_orders

    def _extract_orders_for_year(self, year: int) -> List[OrderData]:
        """
        Extract all orders for a specific year.

        Args:
            year: Year to extract orders for

        Returns:
            List of OrderData objects for the year
        """
        # Navigate to year-specific page
        year_url = f"https://www.amazon.it/your-orders/orders?timeFilter=year-{year}"
        print(f"Navigating to: {year_url}")
        self.driver.get(year_url)

        # Wait for page to load
        WebDriverWait(self.driver, self.wait_timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Extract orders from all pages for this year
        year_orders = []
        page_num = 1

        while True:
            print(f"Processing page {page_num} for year {year}...")

            # Extract orders from current page
            page_orders = self._extract_orders_from_page()
            year_orders.extend(page_orders)

            print(f"Found {len(page_orders)} orders on page {page_num}")

            # Try to go to next page
            if not self._go_to_next_page():
                print(f"No more pages for year {year}")
                break

            page_num += 1
            time.sleep(2)  # Brief pause between pages

        return year_orders

    def _extract_orders_from_page(self) -> List[OrderData]:
        """
        Extract all orders from the current page.

        Returns:
            List of OrderData objects from current page
        """
        orders = []

        try:
            # Store the current order history page URL
            history_page_url = self.driver.current_url

            # Wait for orders to load
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.a-box-group.a-spacing-base"))
            )

            # Find all order cards
            order_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.a-box-group.a-spacing-base")
            print(f"Found {len(order_cards)} order cards")

            # Collect order detail URLs
            order_urls = []
            for card in order_cards:
                try:
                    order_details_link = card.find_element(By.CSS_SELECTOR, "a.a-link-normal[href*='order-details']")
                    url = order_details_link.get_attribute('href')
                    order_urls.append(url)
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"Error getting URL from card: {e}")
                    continue

            # Process each order URL
            for url in order_urls:
                try:
                    # Navigate to order details page
                    self.driver.get(url)
                    WebDriverWait(self.driver, self.wait_timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )

                    # Extract order data
                    order_data = self._extract_single_order()
                    if order_data:
                        orders.append(order_data)

                except Exception as e:
                    print(f"Error processing order: {e}")
                    continue

            # Navigate back to order history page after processing all orders
            self.driver.get(history_page_url)
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

        except TimeoutException:
            print("Timeout waiting for order cards to load")
        except Exception as e:
            print(f"Error extracting orders from page: {e}")

        return orders

    def _extract_single_order(self) -> Optional[OrderData]:
        """
        Extract data from the current order details page.

        Returns:
            OrderData object or None if extraction fails
        """
        try:
            order_data = OrderData()

            # Extract order ID
            order_data.order_id = self._extract_order_id()
            print(f"  Order ID: {order_data.order_id or 'Not found'}")

            # Extract date
            order_data.date = self._extract_date()
            print(f"  Date: {order_data.date or 'Not found'}")

            # Extract amount
            order_data.amount = self._extract_amount()
            print(f"  Amount: {order_data.amount or 'Not found'}")

            # Extract description
            order_data.description = self._extract_description()
            print(f"  Description: {order_data.description or 'Not found'}")

            # Validate extracted data
            if self._validate_order_data(order_data):
                print(f"  Order data valid: {order_data}")
                return order_data
            else:
                print(f"  Invalid order data: {order_data}")
                return None

        except Exception as e:
            print(f"  Error extracting single order: {e}")
            return None

    def _extract_order_id(self) -> str:
        """Extract order ID from the current page."""
        try:
            # Look for the order ID in the specific div with data-component="orderId"
            order_id_element = self.driver.find_element(By.CSS_SELECTOR, "div[data-component='orderId'] span")
            order_id = order_id_element.text.strip()
            return order_id

        except NoSuchElementException:
            return ""
        except Exception:
            return ""

    def _extract_date(self) -> str:
        """Extract order date from the current page."""
        try:
            # Look for the date in the specific div with data-component="orderDate"
            date_element = self.driver.find_element(By.CSS_SELECTOR, "div[data-component='orderDate'] span")
            date_text = date_element.text.strip()
            return date_text

        except NoSuchElementException:
            return ""
        except Exception:
            return ""

    def _extract_amount(self) -> str:
         """Extract order amount from the current page."""
         try:
             # Look for the total amount in the charge summary section
             # Find the bold "Totale:" item (the final total)
             bold_totale_element = self.driver.find_element(By.CSS_SELECTOR, "div[data-component='chargeSummary'] span.a-list-item span.a-text-bold")

             # Get the parent list item to extract the full text
             list_item = bold_totale_element.find_element(By.XPATH, "ancestor::span[@class='a-list-item']")
             text = list_item.text.strip()

             # Extract the monetary amount (digits followed by €)
             euro_match = re.search(r'[\d,]+\.?\d*\s*€', text)
             if euro_match:
                 # Replace € with EUR and format as 'EUR amount'
                 amount = euro_match.group(0).replace('€', '').strip()
                 return f'EUR {amount}'

             return ""

         except Exception:
             return ""

    def _extract_description(self) -> str:
        """Extract order description from the current page."""
        try:
            # Look for item titles in the purchased items section
            item_title_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-component='itemTitle'] a.a-link-normal")

            descriptions = []
            for element in item_title_elements:
                text = element.text.strip()
                if text and len(text) > 3:  # Avoid very short texts
                    descriptions.append(text)

            # Return the most relevant description (usually the first one)
            if descriptions:
                return descriptions[0][:100]  # Limit length

            return "Amazon Order"

        except Exception:
            return "Amazon Order"

    def _validate_order_data(self, order_data: OrderData) -> bool:
        """
        Validate that extracted order data is complete and reasonable.

        Args:
            order_data: OrderData object to validate

        Returns:
            True if data is valid, False otherwise
        """
        # Check required fields
        if not order_data.order_id:
            return False

        if not order_data.date:
            return False

        if not order_data.amount:
            return False

        # Basic format checks
        if not re.match(r'^[A-Z0-9-]+$', order_data.order_id):
            return False

        if not re.match(r'EUR\s*[\d,]+\.?\d*', order_data.amount):
            return False

        return True

    def _go_to_next_page(self) -> bool:
        """
        Navigate to the next page of order history.

        Returns:
            True if navigation successful, False if no more pages
        """
        try:
            # Look for "Next" button or pagination
            next_selectors = [
                "[data-cy='pagination-next']",
                ".a-pagination .a-last a",
                "a[href*='startIndex']"
            ]

            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        next_button.click()
                        time.sleep(3)  # Wait for page to load
                        return True
                except NoSuchElementException:
                    continue

            return False

        except Exception as e:
            print(f"Error navigating to next page: {e}")
            return False