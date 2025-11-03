"""
Data Extractor Module

Scrapes order information from Amazon order history pages.
Extracts transaction details including dates, amounts, descriptions, and merchant info.
"""

import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
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


class ProductData:
    """
    Represents a single product within an Amazon order.
    """

    def __init__(self, date: str = "", product: str = "", quantity: int = 1, price: str = "", shipment_status: str = ""):
        self.date = date
        self.product = product
        self.quantity = quantity
        self.price = price
        self.shipment_status = shipment_status

    def to_dict(self) -> Dict[str, Any]:
        """Convert product data to dictionary format."""
        return {
            'date': self.date,
            'product': self.product,
            'quantity': self.quantity,
            'price': self.price,
            'shipment_status': self.shipment_status
        }

    def __str__(self) -> str:
        return f"Product: {self.product} - Qty: {self.quantity} - Price: {self.price} - Status: {self.shipment_status} on {self.date}"


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

    def extract_orders_by_years(self, start_year: Optional[int] = None, end_year: Optional[int] = None, max_orders: Optional[int] = None) -> tuple[List[OrderData], List[ProductData]]:
        """
        Extract order data for a range of years.

        Args:
            start_year: Starting year (None for current year)
            end_year: Ending year (None for current year)
            max_orders: Maximum number of orders to extract (None for no limit)

        Returns:
            Tuple of (List of OrderData objects, List of ProductData objects)
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
        if max_orders:
            print(f"Limiting to maximum {max_orders} orders")
        all_orders = []
        all_products = []

        for year in range(start_year, end_year + 1):
            # Check if we've already reached the maximum orders
            if max_orders and len(all_orders) >= max_orders:
                print(f"Reached maximum order limit ({max_orders}), stopping extraction")
                break

            remaining_orders = max_orders - len(all_orders) if max_orders else None
            print(f"Processing year {year}... (remaining orders allowed: {remaining_orders or 'unlimited'})")
            year_orders, year_products = self._extract_orders_for_year(year, remaining_orders)
            all_orders.extend(year_orders)
            all_products.extend(year_products)
            print(f"Found {len(year_orders)} orders and {len(year_products)} products for year {year}")

        print(f"Total orders extracted: {len(all_orders)}")
        print(f"Total products extracted: {len(all_products)}")
        return all_orders, all_products

    def _extract_orders_for_year(self, year: int, max_orders: Optional[int] = None) -> tuple[List[OrderData], List[ProductData]]:
        """
        Extract all orders for a specific year.

        Args:
            year: Year to extract orders for
            max_orders: Maximum number of orders to extract for this year (None for no limit)

        Returns:
            Tuple of (List of OrderData objects, List of ProductData objects) for the year
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
        year_products = []
        page_num = 1

        while True:
            print(f"Processing page {page_num} for year {year}...")

            # Check if we've reached the maximum orders for this year
            if max_orders and len(year_orders) >= max_orders:
                print(f"Reached maximum order limit ({max_orders}) for year {year}")
                break

            # Calculate remaining orders for this page
            remaining_for_page = max_orders - len(year_orders) if max_orders else None

            # Extract orders and products from current page
            page_orders, page_products = self._extract_orders_from_page(remaining_for_page)
            year_orders.extend(page_orders)
            year_products.extend(page_products)

            print(f"Found {len(page_orders)} orders and {len(page_products)} products on page {page_num}")

            # Try to go to next page
            if not self._go_to_next_page():
                print(f"No more pages for year {year}")
                break

            page_num += 1
            time.sleep(2)  # Brief pause between pages

        return year_orders, year_products

    def _extract_orders_from_page(self, max_orders: Optional[int] = None) -> tuple[List[OrderData], List[ProductData]]:
        """
        Extract all orders from the current page.

        Args:
            max_orders: Maximum number of orders to extract from this page (None for no limit)

        Returns:
            Tuple of (List of OrderData objects, List of ProductData objects) from current page
        """
        orders = []
        all_products = []

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
                # Check if we've reached the maximum orders for this page
                if max_orders and len(orders) >= max_orders:
                    print(f"Reached maximum order limit ({max_orders}) for this page")
                    break

                try:
                    # Navigate to order details page
                    self.driver.get(url)
                    WebDriverWait(self.driver, self.wait_timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )

                    # Extract order data and products
                    order_data, products = self._extract_single_order()
                    if order_data:
                        orders.append(order_data)
                    # Add products to the global products list
                    all_products.extend(products)

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

        return orders, all_products

    def _extract_single_order(self) -> tuple[Optional[OrderData], List[ProductData]]:
        """
        Extract data from the current order details page.

        Returns:
            Tuple of (OrderData object or None, List of ProductData objects)
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

            # Extract products
            products = self._extract_products(order_data.date)
            print(f"  Products found: {len(products)}")

            # Validate extracted data
            if self._validate_order_data(order_data):
                print(f"  Order data valid: {order_data}")
                return order_data, products
            else:
                print(f"  Invalid order data: {order_data}")
                return None, products

        except Exception as e:
            print(f"  Error extracting single order: {e}")
            return None, []

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

    def _extract_products(self, order_date: str) -> List[ProductData]:
        """
        Extract product details from the current order details page.

        Args:
            order_date: The date of the order to use for all products

        Returns:
            List of ProductData objects
        """
        products = []

        try:
            # Find all order cards (shipments)
            order_cards = self.driver.find_elements(By.CSS_SELECTOR, "div[data-component='orderCard']")

            for card in order_cards:
                try:
                    # Find shipments within the order card
                    shipments = card.find_elements(By.CSS_SELECTOR, "div[data-component='shipments'] div.a-box")

                    for shipment in shipments:
                        try:
                            # Find purchased items within the shipment
                            purchased_items = shipment.find_elements(By.CSS_SELECTOR, "div[data-component='purchasedItems'] div.a-fixed-left-grid")

                            for item in purchased_items:
                                try:
                                    # Extract product title
                                    title_element = item.find_element(By.CSS_SELECTOR, "div[data-component='itemTitle'] a.a-link-normal")
                                    product_title = title_element.text.strip()

                                    # Extract quantity (default to 1 if not found)
                                    quantity = 1
                                    try:
                                        qty_element = item.find_element(By.CSS_SELECTOR, "div.od-item-view-qty span")
                                        quantity = int(qty_element.text.strip())
                                    except NoSuchElementException:
                                        pass  # Keep default quantity of 1

                                    # Extract price
                                    price_element = item.find_element(By.CSS_SELECTOR, "div[data-component='unitPrice'] .a-price .a-offscreen")
                                    price = price_element.get_attribute("textContent").strip().replace('€', '').strip()

                                    # Extract shipment status from the parent shipment
                                    shipment_status = ""
                                    try:
                                        status_element = shipment.find_element(By.CSS_SELECTOR, "div[data-component='shipmentStatus'] h4.a-color-base.od-status-message")
                                        shipment_status = status_element.text.strip()
                                    except NoSuchElementException:
                                        pass  # Keep empty if not found

                                    # Create ProductData object
                                    product = ProductData(
                                        date=order_date,
                                        product=product_title,
                                        quantity=quantity,
                                        price=price,
                                        shipment_status=shipment_status
                                    )
                                    products.append(product)

                                except NoSuchElementException:
                                    continue  # Skip items that can't be parsed
                                except Exception as e:
                                    print(f"Error extracting product data: {e}")
                                    continue

                        except NoSuchElementException:
                            continue  # No purchased items in this shipment
                        except Exception as e:
                            print(f"Error processing shipment: {e}")
                            continue

                except NoSuchElementException:
                    continue  # No shipments in this card
                except Exception as e:
                    print(f"Error processing order card: {e}")
                    continue

        except Exception as e:
            print(f"Error extracting products: {e}")

        return products

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