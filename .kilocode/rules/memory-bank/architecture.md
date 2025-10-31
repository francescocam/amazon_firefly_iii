# System Architecture

## Overview
The Amazon Firefly III integration is a Python-based application that uses browser automation to extract order data from Amazon Italy and convert it into CSV format compatible with Firefly III import.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Browser  │    │   Python App    │    │   Firefly III   │
│   (Slave Mode)  │───▶│   Automation    │───▶│   CSV Import    │
│                 │    │                 │    │                 │
│ • Manual Login  │    │ • Data Extract  │    │ • Transactions  │
│ • MFA/CAPTCHA   │    │ • CSV Generate  │    │ • Categories    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Architecture

### 1. Browser Controller
- **Purpose**: Manages the slave browser session for Amazon access
- **Technology**: Selenium WebDriver with Chrome/Chromium
- **Responsibilities**:
  - Launch browser in controlled environment
  - Navigate to Amazon.it order history
  - Handle page loading and dynamic content
  - Provide interface for user authentication
  - Save and restore browser session data to avoid repeated logins

### 2. Data Extractor
- **Purpose**: Scrapes order information from Amazon pages
- **Technology**: Selenium locators and parsing logic
- **Responsibilities**:
  - Identify order elements on page
  - Extract transaction details (date, amount, description, merchant)
  - Handle pagination through order history
  - Validate data completeness

### 3. Data Processor
- **Purpose**: Transforms raw data into Firefly III format
- **Technology**: Python data manipulation libraries
- **Responsibilities**:
  - Clean and normalize extracted data
  - Map Amazon fields to Firefly III CSV schema
  - Handle currency conversion if needed
  - Generate properly formatted CSV output

### 4. Configuration Manager
- **Purpose**: Manages application settings and user preferences
- **Technology**: Configuration files (JSON/YAML)
- **Responsibilities**:
  - Store date range preferences
  - Manage output file locations
  - Handle Firefly III import settings

## Data Flow

1. **Initialization**: User launches app, browser opens in slave mode, attempts to restore previous session if available
2. **Authentication**: If no valid session, user manually logs into Amazon.it (handles MFA/CAPTCHA); otherwise proceeds with restored session
3. **Navigation**: App navigates to order history page
4. **Extraction**: App iterates through orders, extracting data
5. **Processing**: Raw data is cleaned and formatted
6. **Session Save**: Browser session data saved for future use
7. **Output**: CSV file generated for Firefly III import

## Key Design Decisions

### Slave Browser Approach
- **Rationale**: Avoids storing credentials and handles dynamic security measures
- **Benefits**: Secure, adaptable to Amazon's changing authentication requirements
- **Trade-offs**: Requires user interaction for initial login

### CSV Output Format
- **Rationale**: Firefly III supports CSV import as standard feature
- **Benefits**: No API integration needed, works with self-hosted instances
- **Trade-offs**: Manual import step required by user

### Python Implementation
- **Rationale**: Rich ecosystem for web scraping and data processing
- **Benefits**: Mature libraries (Selenium, pandas), cross-platform compatibility
- **Trade-offs**: Requires Python environment setup

## Security Considerations

- No credential storage - user maintains control of authentication
- Browser automation runs locally, no data transmission to external servers
- Generated CSV files contain only transaction data, no sensitive information

## Error Handling

- Graceful handling of page layout changes
- Retry mechanisms for network issues
- Clear error messages for user troubleshooting
- Fallback options for partial data extraction