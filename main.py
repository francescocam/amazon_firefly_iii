#!/usr/bin/env python3
"""
Amazon Firefly III Integration - Main Entry Point

Extracts Amazon Italy order data and converts it to Firefly III CSV format.
Uses browser automation to handle login and data extraction securely.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import Config
from src.browser_controller import BrowserController
from src.data_extractor import DataExtractor
from src.data_processor import DataProcessor
from src.cache_manager import CacheManager


def setup_logging(debug: bool = False) -> None:
    """
    Setup logging configuration.

    Args:
        debug: Enable debug logging if True
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Extract Amazon Italy orders and convert to Firefly III CSV format'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/settings.json',
        help='Path to configuration file (default: config/settings.json)'
    )


    parser.add_argument(
        '--start-year',
        type=int,
        default=None,
        help='Start year for order extraction (default: current year)'
    )

    parser.add_argument(
        '--end-year',
        type=int,
        default=None,
        help='End year for order extraction (default: current year)'
    )

    parser.add_argument(
        '--max-orders',
        type=int,
        default=None,
        help='Maximum number of orders to extract (default: no limit)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV file path (default: auto-generated)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--no-session-save',
        action='store_true',
        help='Do not save browser session for future use'
    )

    parser.add_argument(
        '--use-cache',
        type=str,
        default=None,
        help='Use cached data instead of scraping (specify cache name or "latest")'
    )

    parser.add_argument(
        '--save-cache',
        action='store_true',
        help='Save extracted data to cache for future use'
    )

    parser.add_argument(
        '--cache-dir',
        type=str,
        default='cache',
        help='Directory for cache files (default: cache)'
    )

    parser.add_argument(
        '--list-cache',
        action='store_true',
        help='List available cache directories and exit'
    )

    return parser.parse_args()


def main() -> int:
    """
    Main application entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Setup logging
        setup_logging(args.debug)

        print("Amazon Firefly III Integration")
        print("=" * 40)

        # Load configuration
        config = Config(args.config)
        if not config.validate():
            logging.warning("Configuration validation failed, but continuing...")

        # Override config with command line args
        if args.start_year:
            config.set('start_year', args.start_year)
        if args.end_year:
            config.set('end_year', args.end_year)
        if args.max_orders:
            config.set('max_orders', args.max_orders)

        logging.info(f"Configuration loaded from {args.config}")

        # Handle cache listing
        if args.list_cache:
            cache_manager = CacheManager(args.cache_dir)
            cache_dirs = cache_manager.list_cache_directories()
            if cache_dirs:
                print("Available cache directories:")
                for cache_dir in sorted(cache_dirs, reverse=True):
                    info = cache_manager.get_cache_info(cache_dir)
                    print(f"  {cache_dir}: {info.get('orders_count', 0)} orders, {info.get('products_count', 0)} products")
            else:
                print("No cache directories found.")
            return 0

        # Display testing information
        print("DEBUG MODE ENABLED - Detailed logging active" if args.debug else "Standard logging mode")
        print(f"Year range: {config.get('start_year', 'current')} - {config.get('end_year', 'current')}")
        print(f"Max orders: {config.get('max_orders', 'no limit')}")
        print(f"Session saving: {'Disabled' if args.no_session_save else 'Enabled'}")
        print(f"Cache mode: {'Use cache' if args.use_cache else 'Extract fresh' if not args.save_cache else 'Extract and save cache'}")
        print()

        # Initialize components
        cache_manager = CacheManager(args.cache_dir)
        data_processor = DataProcessor(config)

        success = False

        # Handle cache usage
        if args.use_cache:
            try:
                print(f"Loading data from cache: {args.use_cache}")
                orders, products = cache_manager.load_cache(args.use_cache)

                if not orders:
                    logging.warning("No orders found in cache")
                    return 1

            except Exception as e:
                logging.error(f"Failed to load cache: {e}")
                return 1

        else:
            # Normal extraction flow
            browser_controller = BrowserController(config)
            data_extractor = None

            # Start browser manually to keep it open for user interaction
            browser_controller.start_browser()

            try:
                # Check if already logged in
                if not browser_controller.is_logged_in():
                    print("\n" + "="*60)
                    print("AMAZON LOGIN REQUIRED")
                    print("="*60)
                    print("A browser window has opened with Amazon.it")
                    print("Please complete the following steps:")
                    print("  1. Log in to your Amazon.it account")
                    print("  2. Complete any MFA (2FA) requirements")
                    print("  3. Solve any CAPTCHA if presented")
                    print("  4. Navigate to your account if redirected")
                    print()
                    print("The application will automatically continue once login is detected.")
                    print("You have 5 minutes to complete the login process.")
                    print("="*60 + "\n")

                    if not browser_controller.wait_for_user_login():
                        print("\nLOGIN TIMEOUT")
                        print("Login was not completed within 5 minutes.")
                        print("Please try running the application again.")
                        logging.error("Login failed or timed out")
                        browser_controller.close_browser()
                        return 1

                    print("\nLOGIN SUCCESSFUL")
                    print("Login detected! Saving session for future use...\n")

                    # Save session immediately after successful login
                    if not args.no_session_save:
                        browser_controller.save_session()
                        print("Session saved successfully.\n")
                    else:
                        print("Session saving disabled.\n")

                # Navigate to order history (will be handled by data extractor for year-specific navigation)
                # The data extractor will handle navigation to appropriate year pages

                # Extract order data
                data_extractor = DataExtractor(browser_controller.driver, config)
                start_year = config.get('start_year')
                end_year = config.get('end_year')
                max_orders = config.get('max_orders')
                orders, products = data_extractor.extract_orders_by_years(start_year, end_year, max_orders)

                if not orders:
                    logging.warning("No orders found to process")
                    browser_controller.close_browser()
                    return 1

                # Save to cache if requested
                if args.save_cache:
                    try:
                        cache_path = cache_manager.save_cache(orders, products)
                        print(f"Data cached to: {cache_path}")
                    except Exception as e:
                        logging.warning(f"Failed to save cache: {e}")

            finally:
                # Always close the browser
                browser_controller.close_browser()

        # Process and generate CSVs
        print(f"Processing {len(orders)} orders and {len(products)} products...")

        # Generate orders CSV
        orders_csv_path = data_processor.process_orders(orders)

        # Generate products CSV
        products_csv_path = data_processor.process_products(products)

        # Validate orders CSV for Firefly III compatibility
        print("Validating orders CSV for Firefly III compatibility...")
        if data_processor.validate_csv_for_firefly(orders_csv_path):
            print(f"\nSUCCESS! Orders CSV file generated: {orders_csv_path}")
            print(f"Products CSV file generated: {products_csv_path}")
            print("You can now import these files into your Firefly III instance.")
            success = True
        else:
            print("\nOrders CSV validation failed")
            logging.error("Generated orders CSV failed validation")
            return 1

        # Save session if successful and not disabled (only if we used browser)
        if success and not args.no_session_save and not args.use_cache:
            try:
                browser_controller.save_session()
            except NameError:
                pass  # browser_controller not defined when using cache

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def show_usage_info() -> None:
    """
    Display usage information and requirements.
    """
    print("""
Amazon Firefly III Integration

USAGE:
    python main.py [options]

OPTIONS:
    --config FILE       Configuration file path (default: config/settings.json)
    --start-year YEAR   Start year for order extraction (default: current year)
    --end-year YEAR     End year for order extraction (default: current year)
    --max-orders NUM    Maximum number of orders to extract (default: no limit)
    --output FILE       Output CSV file path (default: auto-generated)
    --debug             Enable debug logging
    --no-session-save   Don't save browser session
    --use-cache NAME    Use cached data instead of scraping (specify cache name or "latest")
    --save-cache        Save extracted data to cache for future use
    --cache-dir DIR     Directory for cache files (default: cache)
    --list-cache        List available cache directories and exit

REQUIREMENTS:
    - Python 3.8+
    - Chrome or Chromium browser
    - Valid Amazon.it account

WORKFLOW:
    1. Run the application
    2. Log in to Amazon.it when prompted (first run only)
    3. Wait for automatic data extraction
    4. Import generated CSV into Firefly III

For more information, see README.md
    """)


if __name__ == '__main__':
    # Show usage if no arguments provided
    if len(sys.argv) == 1:
        show_usage_info()
        sys.exit(0)

    # Run main application
    exit_code = main()
    sys.exit(exit_code)