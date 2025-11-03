"""
Cache Manager Module

Handles serialization and deserialization of scraped order and product data
for debugging and re-processing without re-scraping.
"""

import os
import json
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path

from .data_extractor import OrderData, ProductData


class CacheManager:
    """
    Manages caching of extracted order and product data.

    Provides functionality to save and load scraped data to/from JSON files
    for debugging and re-processing purposes.
    """

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Base directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def save_cache(self, orders: List[OrderData], products: List[ProductData],
                   cache_name: Optional[str] = None) -> str:
        """
        Save orders and products data to cache files.

        Args:
            orders: List of OrderData objects
            products: List of ProductData objects
            cache_name: Optional name for cache directory (default: timestamp)

        Returns:
            Path to the cache directory
        """
        if cache_name is None:
            cache_name = datetime.now().strftime('%Y%m%d_%H%M%S')

        cache_path = self.cache_dir / cache_name
        cache_path.mkdir(exist_ok=True)

        # Save orders
        orders_data = [order.to_dict() for order in orders]
        orders_file = cache_path / "orders.json"
        with open(orders_file, 'w', encoding='utf-8') as f:
            json.dump(orders_data, f, indent=2, ensure_ascii=False)

        # Save products
        products_data = [product.to_dict() for product in products]
        products_file = cache_path / "products.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)

        # Update latest symlink
        self._update_latest_symlink(cache_path)

        print(f"Cache saved to: {cache_path}")
        return str(cache_path)

    def load_cache(self, cache_name: Optional[str] = None) -> Tuple[List[OrderData], List[ProductData]]:
        """
        Load orders and products data from cache files.

        Args:
            cache_name: Name of cache directory (default: 'latest')

        Returns:
            Tuple of (orders, products) lists

        Raises:
            FileNotFoundError: If cache files don't exist
            ValueError: If cache data is invalid
        """
        if cache_name is None:
            cache_name = "latest"

        cache_path = self.cache_dir / cache_name

        # Resolve symlink if 'latest'
        if cache_name == "latest" and cache_path.is_symlink():
            cache_path = cache_path.resolve()

        if not cache_path.exists():
            raise FileNotFoundError(f"Cache directory not found: {cache_path}")

        orders_file = cache_path / "orders.json"
        products_file = cache_path / "products.json"

        if not orders_file.exists() or not products_file.exists():
            raise FileNotFoundError(f"Cache files not found in: {cache_path}")

        # Load orders
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders_data = json.load(f)

        orders = []
        for item in orders_data:
            try:
                order = OrderData(
                    order_id=item.get('order_id', ''),
                    date=item.get('date', ''),
                    amount=item.get('amount', ''),
                    description=item.get('description', ''),
                    merchant=item.get('merchant', 'Amazon')
                )
                orders.append(order)
            except Exception as e:
                print(f"Warning: Failed to load order from cache: {e}")
                continue

        # Load products
        with open(products_file, 'r', encoding='utf-8') as f:
            products_data = json.load(f)

        products = []
        for item in products_data:
            try:
                product = ProductData(
                    date=item.get('date', ''),
                    product=item.get('product', ''),
                    quantity=item.get('quantity', 1),
                    price=item.get('price', ''),
                    shipment_status=item.get('shipment_status', '')
                )
                products.append(product)
            except Exception as e:
                print(f"Warning: Failed to load product from cache: {e}")
                continue

        print(f"Cache loaded from: {cache_path}")
        print(f"Loaded {len(orders)} orders and {len(products)} products")

        return orders, products

    def list_cache_directories(self) -> List[str]:
        """
        List all available cache directories.

        Returns:
            List of cache directory names
        """
        if not self.cache_dir.exists():
            return []

        return [d.name for d in self.cache_dir.iterdir()
                if d.is_dir() and not d.name.startswith('.')]

    def get_cache_info(self, cache_name: Optional[str] = None) -> dict:
        """
        Get information about a cache directory.

        Args:
            cache_name: Name of cache directory (default: 'latest')

        Returns:
            Dictionary with cache information
        """
        if cache_name is None:
            cache_name = "latest"

        cache_path = self.cache_dir / cache_name

        # Resolve symlink if 'latest'
        if cache_name == "latest" and cache_path.is_symlink():
            cache_path = cache_path.resolve()

        if not cache_path.exists():
            return {"error": f"Cache directory not found: {cache_path}"}

        orders_file = cache_path / "orders.json"
        products_file = cache_path / "products.json"

        info = {
            "cache_name": cache_name,
            "cache_path": str(cache_path),
            "orders_file_exists": orders_file.exists(),
            "products_file_exists": products_file.exists(),
            "orders_count": 0,
            "products_count": 0
        }

        # Try to get counts
        try:
            if orders_file.exists():
                with open(orders_file, 'r', encoding='utf-8') as f:
                    orders_data = json.load(f)
                    info["orders_count"] = len(orders_data)

            if products_file.exists():
                with open(products_file, 'r', encoding='utf-8') as f:
                    products_data = json.load(f)
                    info["products_count"] = len(products_data)
        except Exception as e:
            info["error"] = f"Failed to read cache files: {e}"

        return info

    def _update_latest_symlink(self, cache_path: Path) -> None:
        """
        Update the 'latest' symlink to point to the given cache directory.

        Args:
            cache_path: Path to the cache directory
        """
        latest_link = self.cache_dir / "latest"

        try:
            # Remove existing symlink if it exists
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()

            # Create new symlink (relative path for portability)
            latest_link.symlink_to(cache_path.name, target_is_directory=True)
        except OSError:
            # Symlinks might not be supported on all systems (e.g., Windows without privileges)
            print("Warning: Could not create 'latest' symlink (may not be supported on this system)")
            pass