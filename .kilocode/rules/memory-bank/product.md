# Product Description

## Why This Project Exists

This project addresses the need for seamless financial data integration between Amazon Italy orders and personal finance management through Firefly III. Users who make frequent purchases on Amazon need an automated way to import their order data into their self-hosted Firefly III instance for better expense tracking and budgeting.

## Problems It Solves

1. **Manual Data Entry Burden**: Eliminates the tedious process of manually entering Amazon order details into Firefly III
2. **Login and Security Challenges**: Bypasses Amazon's login restrictions, CAPTCHAs, and MFA requirements by using a slave browser approach
3. **Data Accuracy**: Ensures accurate extraction of order information including dates, amounts, descriptions, and merchant details
4. **Time Savings**: Automates the extraction and formatting process, saving users significant time

## How It Should Work

1. **User Authentication**: User manually logs into Amazon.it through a controlled browser session
2. **Order Extraction**: Application automatically navigates through order history and extracts relevant transaction data
3. **Data Processing**: Raw order data is cleaned, formatted, and transformed into Firefly III compatible CSV format
4. **Import Ready**: Generated CSV file can be directly imported into Firefly III for expense categorization and tracking

## User Experience Goals

- **Simple Setup**: Minimal configuration required beyond Amazon login
- **Reliable Operation**: Handles various Amazon page layouts and updates gracefully
- **Secure**: No storage of sensitive login credentials; user maintains control of authentication
- **Transparent**: Clear feedback on extraction progress and any issues encountered
- **Flexible**: Configurable date ranges and order filtering options