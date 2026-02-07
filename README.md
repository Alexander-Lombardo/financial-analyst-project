# SEC Filing Browser

A Flask web application for browsing and analyzing SEC filings. Provides a clean interface to search companies, view filing lists, and read individual 10-K and 10-Q filings with parsed financial statements.

## Features

- **Company Search**: Search for companies by ticker symbol or name
- **Filing List**: View all SEC filings for a company with filtering by form type and year
- **Focused View**: Parsed financial statements with clean, readable formatting
- **Full Filing View**: Original SEC filing content

## Financial Statement Parsing

The filing parser (`filing_parser.py`) extracts and formats the following statements:

### Income Statement
- Extracts from "Consolidated Statements of Operations/Income/Earnings"
- Displays revenues, expenses, and net income with proper column alignment

### Balance Sheet
- Extracts from "Consolidated Balance Sheets"
- Shows assets, liabilities, and shareholders' equity

### Cash Flow Statement
- Extracts from "Consolidated Statements of Cash Flows"
- Operating, investing, and financing activities

### Shareholders' Equity
- Extracts from "Consolidated Statements of Stockholders'/Shareholders' Equity"
- Shows changes in equity components over time

### Retained Earnings
Intelligent extraction that handles both filing formats:

- **10-K (Annual)**: Extracts the dedicated "Retained Earnings:" section showing:
  - Beginning balance
  - Net income
  - Dividends
  - Ending balance

- **10-Q (Quarterly)**: Extracts retained earnings activity from the columnar equity statement:
  - Quarterly beginning/ending balances
  - Net income contributions
  - Dividend declarations

## Table Formatting

All financial tables are cleaned and formatted for readability:
- Empty columns removed
- Values properly aligned
- Section headers preserved
- Numeric data formatted consistently

## Running the Application

```bash
# Set port (optional, defaults to 5000)
export PORT=5003

# Run the application
python3 app.py
```

Then open `http://localhost:5003` in your browser.

## Project Structure

```
├── app.py              # Flask web application
├── filing_parser.py    # SEC filing parser for financial statements
├── cik_resolver.py     # Company CIK lookup and filing retrieval
├── sec_data_fetcher.py # SEC EDGAR API client
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── company.html
│   ├── filing_focused.html
│   └── filing_full.html
└── static/             # CSS and JavaScript assets
```

## Dependencies

- Flask
- BeautifulSoup4
- Requests

## Usage Examples

1. **View Home Depot 10-K**:
   ```
   http://localhost:5003/view/HD/0000354950-25-000085
   ```

2. **View Walmart 10-Q**:
   ```
   http://localhost:5003/view/WMT/0000104169-25-000191
   ```

3. **Search for a company**:
   ```
   http://localhost:5003/search?q=apple
   ```
