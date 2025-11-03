# Technology Stack

## Core Technologies

### Python
- **Version**: 3.8+
- **Purpose**: Main application language
- **Rationale**: Rich ecosystem for web scraping, data processing, and automation

### Selenium WebDriver
- **Purpose**: Browser automation for Amazon order extraction
- **Configuration**: Chrome/Chromium driver with headless option
- **Features Used**:
  - Web element selection and interaction
  - Page navigation and waiting
  - Screenshot capabilities for debugging
  - Session data persistence (cookies, local storage)

### Data Processing Libraries
- **pandas**: Data manipulation and CSV generation
- **datetime**: Date parsing and formatting
- **csv**: Standard CSV file handling

## Development Environment

### Virtual Environment
- **Tool**: venv (Python built-in)
- **Location**: `.venv` folder in project root
- **Activation**: `source .venv/bin/activate` (Unix) or `.venv\Scripts\activate` (Windows)

### Package Management
- **Tool**: pip
- **Requirements File**: `requirements.txt`
- **Virtual Environment Usage**: All pip commands must use the activated virtual environment

## Dependencies

### Core Dependencies
```
selenium>=4.15.0
pandas>=2.0.0
webdriver-manager>=4.0.0
```

### Development Dependencies
```
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
```

## Project Structure

```
amazon_firefly_iii/
├── src/
│   ├── __init__.py
│   ├── browser_controller.py
│   ├── data_extractor.py
│   ├── data_processor.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_browser_controller.py
│   ├── test_data_extractor.py
│   └── test_data_processor.py
├── config/
│   └── settings.json
├── cache/                       # Cached scraped data (JSON)
├── output/                      # Generated CSV files
├── requirements.txt
├── main.py
└── README.md
```

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Chrome or Chromium browser
- Git (for version control)

### Installation Steps
1. Clone repository
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Install Chrome WebDriver: handled automatically by webdriver-manager

### Running the Application
```bash
python main.py
```

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (browser, file system)
- Focus on data transformation logic

### Integration Tests
- Test end-to-end data flow
- Use test Amazon pages or mock responses
- Validate CSV output format

### Manual Testing
- Browser compatibility testing
- Amazon page layout changes
- Error handling scenarios

## Build and Deployment

### Packaging
- **Tool**: setuptools
- **Output**: Wheel package (.whl)
- **Entry Points**: Console script for easy execution

### Distribution
- **Target**: Local installation only
- **Installation**: `pip install .`
- **Usage**: `amazon-firefly-iii` command

## Technical Constraints

### Browser Automation
- Must handle dynamic Amazon page layouts
- Respect rate limiting and anti-bot measures
- Support both headless and interactive modes

### Data Processing
- Handle multiple currencies (primarily EUR for Amazon.it)
- Support various date formats from Amazon
- Ensure Firefly III CSV schema compliance

### Performance
- Process reasonable order volumes (1000+ orders)
- Minimize memory usage for large datasets
- Provide progress feedback for long operations

## Tool Usage Patterns

### Code Quality
- **Linting**: flake8 for style checking
- **Formatting**: black for consistent formatting
- **Type Hints**: Use typing module for better code documentation

### Version Control
- **Branching**: feature branches for new functionality
- **Commits**: Clear, descriptive commit messages
- **Tags**: Version tags for releases

### Documentation
- **Code Comments**: Docstrings for all public functions
- **README**: Setup and usage instructions
- **Memory Bank**: Project knowledge base