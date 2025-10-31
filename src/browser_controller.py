"""
Browser Controller Module

Manages the slave browser session for Amazon access using Selenium WebDriver.
Handles browser launch, navigation, session persistence, and user authentication.
"""

import os
import pickle
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from .config import Config


class BrowserController:
    """
    Manages browser automation for Amazon order extraction.

    This class handles:
    - Browser initialization and configuration
    - Session data persistence (cookies, local storage)
    - Navigation to Amazon pages
    - User authentication flow
    """

    def __init__(self, config: Config):
        """
        Initialize the browser controller.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.driver = None
        self.session_file = config.get('session_file', 'config/session.pkl')

    def _setup_chrome_options(self) -> Options:
        """
        Configure Chrome options for browser automation.

        Returns:
            Configured Chrome options
        """
        options = Options()

        # Basic options for automation
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        # User agent to mimic regular browser
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )

        # Disable automation indicators
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        return options

    def _create_driver(self) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver instance.

        Returns:
            Configured Chrome WebDriver
        """
        options = self._setup_chrome_options()

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            return driver

        except WebDriverException as e:
            raise RuntimeError(f"Failed to create Chrome driver: {e}")

    def start_browser(self) -> None:
         """
         Start the browser and attempt to restore previous session.
         """
         print("Starting browser...")
         self.driver = self._create_driver()
 
         # Try to restore session if it exists
         if os.path.exists(self.session_file):
             print("Attempting to restore previous session...")
             try:
                 self._restore_session()
                 print("Session restored successfully.")
                 # Navigate to orders page to verify session validity
                 if not self.navigate_to_orders():
                     print("Failed to navigate to orders page after session restore.")
                     print("Please log in manually.")
             except Exception as e:
                 print(f"Failed to restore session: {e}")
                 print("Please log in manually.")
                 # Navigate to Amazon homepage for manual login
                 try:
                     self.driver.get(self.config.get('amazon_url'))
                 except Exception as nav_e:
                     print(f"Failed to navigate to Amazon: {nav_e}")
         else:
             print("No previous session found. Please log in manually.")
             # Navigate to Amazon homepage for manual login
             try:
                 self.driver.get(self.config.get('amazon_url'))
             except Exception as e:
                 print(f"Failed to navigate to Amazon: {e}")

    def _restore_session(self) -> None:
        """
        Restore browser session from saved data.
        """
        if not self.driver:
            return

        with open(self.session_file, 'rb') as f:
            session_data = pickle.load(f)

        # Restore cookies
        if 'cookies' in session_data:
            self.driver.get(self.config.get('amazon_url'))
            for cookie in session_data['cookies']:
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    continue  # Skip invalid cookies

        # Restore local storage if available
        if 'local_storage' in session_data:
            for key, value in session_data['local_storage'].items():
                try:
                    self.driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
                except Exception:
                    continue

    def save_session(self) -> None:
        """
        Save current browser session data for future use.
        Creates backup of existing session before overwriting.
        """
        if not self.driver:
            return

        try:
            session_data = {}

            # Save cookies
            session_data['cookies'] = self.driver.get_cookies()

            # Save local storage
            local_storage = self.driver.execute_script(
                "var items = {}; "
                "for (var i = 0; i < localStorage.length; i++) { "
                "  var key = localStorage.key(i); "
                "  items[key] = localStorage.getItem(key); "
                "} "
                "return items;"
            )
            session_data['local_storage'] = local_storage

            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)

            # Create backup of existing session if it exists
            if os.path.exists(self.session_file):
                backup_file = f"{self.session_file}.backup"
                os.rename(self.session_file, backup_file)
                print(f"Existing session backed up to {backup_file}")

            # Save to file
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)

            print(f"Session saved to {self.session_file}")

        except Exception as e:
            print(f"Failed to save session: {e}")

    def navigate_to_orders(self, year: Optional[int] = None) -> bool:
        """
        Navigate to Amazon order history page, optionally for a specific year.

        Args:
            year: Year to navigate to (None for default order history)

        Returns:
            True if navigation successful, False otherwise
        """
        if not self.driver:
            return False

        try:
            if year:
                # Navigate to year-specific order history
                year_url = f"https://www.amazon.it/your-orders/orders?timeFilter=year-{year}"
                print(f"Navigating to orders for year {year}: {year_url}")
                self.driver.get(year_url)
            else:
                # Navigate to default order history
                order_url = self.config.get('order_history_url')
                print(f"Navigating to {order_url}")
                self.driver.get(order_url)

            # Wait for page to load
            WebDriverWait(self.driver, self.config.get('page_load_timeout', 30)).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            return True

        except TimeoutException:
            print("Timeout waiting for order history page to load")
            return False
        except Exception as e:
            print(f"Error navigating to orders: {e}")
            return False

    def wait_for_user_login(self) -> bool:
        """
        Wait for user to complete manual login process.

        Returns:
            True if login appears successful, False otherwise
        """
        if not self.driver:
            return False

        # Navigate to signin page
        # signin_url = "https://www.amazon.it/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.it%2F%3Flanguage%3Dit_IT%26ref_%3Dnav_ya_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=itflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
        signin_url = (
            "https://www.amazon.it/ap/signin?"
            "openid.pape.max_auth_age=0&"
            "openid.return_to=https%3A%2F%2Fwww.amazon.it%2F%3Flanguage%3Dit_IT%26ref_%3Dnav_ya_signin&"
            "openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&"
            "openid.assoc_handle=itflex&"
            "openid.mode=checkid_setup&"
            "openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&"
            "openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
            )
        
        self.driver.get(signin_url)

        print("Waiting for login completion...")
        print("(Checking every 5 seconds for login status)")

        max_wait = 300  # 5 minutes max wait
        check_interval = 5

        for elapsed in range(0, max_wait, check_interval):
            try:
                # Get current URL for checks
                current_url = self.driver.current_url

                # Try to find an element that indicates logged-in state
                try:
                    self.driver.find_element(By.ID, "nav-item-switch-account")
                    print(f"Login confirmed! (after {elapsed}s)")
                    return True
                except:
                    pass

                # # Check if we're still on the signin page
                # if "/ap/signin" in current_url:
                #     if elapsed % 30 == 0:  # Show progress every 30 seconds
                #         remaining = max_wait - elapsed
                #         print(f"Still waiting for login... ({remaining}s remaining)")
                # else:
                #     # No longer on signin page, assuming login successful
                #     print(f"No longer on signin page, assuming login successful (after {elapsed}s)")
                #     return True

            except Exception as e:
                print(f"Warning: Error checking login status: {e}")

            time.sleep(check_interval)

        print("Login timeout - 5 minutes elapsed")
        print("Please ensure you completed login in the browser window")
        return False

    def is_logged_in(self) -> bool:
        """
        Check if user is currently logged in to Amazon.

        Returns:
            True if logged in, False otherwise
        """
        if not self.driver:
            return False

        try:
            # Check for account link which indicates logged-in state
            self.driver.find_element(By.ID, "nav-item-switch-account")
            return True
        except:
            return False

    def close_browser(self) -> None:
        """
        Close the browser and cleanup resources.
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing browser: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        """Context manager entry."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_browser()