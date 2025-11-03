# Amazon Firefly III Integration

A Python application that extracts order data from Amazon Italy and converts it to CSV format compatible with Firefly III import.

## Features

- **Secure Browser Automation**: Uses Selenium WebDriver with a slave browser approach to handle login and security challenges
- **Session Persistence**: Saves browser session data to avoid repeated logins
- **Data Extraction**: Automatically scrapes order information including dates, amounts, and descriptions
- **Data Caching**: Cache scraped data for debugging and re-processing without re-scraping
- **Firefly III Compatibility**: Generates CSV files in the correct format for Firefly III import
- **Italian Language Support**: Handles Italian date formats and Amazon.it interface

## Requirements

- Python 3.8 or higher
- Chrome or Chromium browser
- Valid Amazon.it account

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd amazon_firefly_iii
```

2. Create virtual environment:
```bash
python -m venv .venv
```

3. Activate virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Unix/Linux
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python main.py
```

### Command Line Options

```bash
python main.py [options]

Options:
  --config FILE       Configuration file path (default: config/settings.json)
  --start-year YEAR   Start year for order extraction (default: current year)
  --end-year YEAR     End year for order extraction (default: current year)
  --output FILE       Output CSV file path (default: auto-generated)
  --debug             Enable debug logging
  --no-session-save   Don't save browser session
  --use-cache NAME    Use cached data instead of scraping (specify cache name or "latest")
  --save-cache        Save extracted data to cache for future use
  --cache-dir DIR     Directory for cache files (default: cache)
  --list-cache        List available cache directories and exit
```

### First Run Workflow

1. **Launch Application**: Run `python main.py`
2. **Browser Opens**: Chrome will open in automation mode
3. **Manual Login**: Log in to Amazon.it and complete any MFA/CAPTCHA
4. **Automatic Processing**: The application detects login and begins data extraction
5. **CSV Generation**: Order data is processed and saved to CSV file

### Subsequent Runs

- The application will attempt to restore your previous session
- If session restoration fails, you'll need to log in again
- Session data is automatically saved after successful processing

### Caching for Debugging

The application supports caching scraped data to enable debugging the data processor without re-scraping:

```bash
# Extract and save data to cache
python main.py --save-cache

# Use cached data for debugging
python main.py --use-cache latest

# List available cache directories
python main.py --list-cache

# Process different year range using cached data
python main.py --use-cache latest --start-year 2023 --end-year 2024
```

Cache files are stored in JSON format in the `cache/` directory with timestamps.

## Configuration

Edit `config/settings.json` to customize behavior:

```json
{
  "amazon_url": "https://www.amazon.it",
  "order_history_url": "https://www.amazon.it/gp/your-account/order-history",
  "output_dir": "output",
  "session_file": "config/session.pkl",
  "date_format": "%Y-%m-%d",
  "max_orders_per_page": 10,
  "page_load_timeout": 30,
  "element_wait_timeout": 10
}
```

## Firefly III Import

1. Log in to your Firefly III instance
2. Go to "Import" section
3. Choose CSV import
4. Upload the generated CSV file
5. Map columns if necessary
6. Complete the import process

## Security Notes

- **No Credential Storage**: The application never stores your Amazon login credentials
- **Local Processing**: All data extraction and processing happens locally
- **Session Data**: Only browser session data (cookies, local storage) is saved locally
- **User Control**: You maintain full control over the authentication process

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
    - Ensure Chrome/Chromium is installed
    - The webdriver-manager will automatically download the correct driver

2. **Login Problems**
    - Try clearing browser data: `rm config/session.pkl`
    - Check Amazon.it for any account security measures

3. **Data Extraction Failures**
    - Amazon may have changed their page layout
    - Enable debug mode: `python main.py --debug`

4. **Cache Issues**
    - Cache files not found: Check if cache directory exists and has data
    - Invalid cache data: Delete corrupted cache and re-extract
    - Permission issues: Ensure write access to cache directory

5. **CSV Import Issues**
    - Verify the CSV format matches Firefly III requirements
    - Check date formats and amount formatting

### Debug Mode

Run with `--debug` flag for detailed logging:

```bash
python main.py --debug
```

## Development

### Project Structure

```
amazon_firefly_iii/
├── src/
│   ├── __init__.py
│   ├── browser_controller.py    # Browser automation
│   ├── cache_manager.py         # Data caching for debugging
│   ├── data_extractor.py        # Order data extraction
│   ├── data_processor.py        # CSV generation
│   └── config.py               # Configuration management
├── tests/
│   ├── __init__.py
│   └── ...                     # Unit tests
├── config/
│   └── settings.json           # Configuration file
├── cache/                      # Cached scraped data (JSON)
├── output/                     # Generated CSV files
├── requirements.txt            # Python dependencies
├── main.py                     # Application entry point
└── README.md                   # This file
```

### Running Tests

```bash
python -m pytest tests/
```

### Code Quality

```bash
# Linting
flake8 src/

# Formatting
black src/
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]