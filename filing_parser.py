"""
Filing Parser Module - Extracts financial statements and MD&A from SEC filings.
Parses HTML/XBRL content to extract structured financial data.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup


class FilingParser:
    """Parser for SEC filing documents to extract financial statements and MD&A."""

    # Common table header patterns for financial statements
    INCOME_STATEMENT_PATTERNS = [
        r'consolidated\s+statements?\s+of\s+(operations?|income|earnings)',
        r'statements?\s+of\s+(operations?|income|earnings)',
        r'income\s+statements?',
        r'operations?\s+statements?',
    ]

    BALANCE_SHEET_PATTERNS = [
        r'consolidated\s+balance\s+sheets?',
        r'balance\s+sheets?',
        r'consolidated\s+statements?\s+of\s+financial\s+(position|condition)',
        r'statements?\s+of\s+financial\s+(position|condition)',
    ]

    CASH_FLOW_PATTERNS = [
        r'consolidated\s+statements?\s+of\s+cash\s+flows?',
        r'statements?\s+of\s+cash\s+flows?',
        r'cash\s+flow\s+statements?',
    ]

    EQUITY_PATTERNS = [
        r'consolidated\s+statements?\s+of\s+(stockholders?|shareholders?)[\'|\u2019]?\s+equity',
        r'statements?\s+of\s+(stockholders?|shareholders?)[\'|\u2019]?\s+equity',
        r'(stockholders?|shareholders?)[\'|\u2019]?\s+equity',
        r'changes\s+in\s+(stockholders?|shareholders?)[\'|\u2019]?\s+equity',
    ]

    RETAINED_EARNINGS_PATTERNS = [
        r'statements?\s+of\s+retained\s+earnings',
        r'consolidated\s+statements?\s+of\s+retained\s+earnings',
    ]

    # MD&A section patterns
    MDA_10K_PATTERNS = [
        r'item\s*7[.\s]*management[\'|\u2019]?s?\s+discussion\s+and\s+analysis',
        r'item\s*7[.\s]*md&a',
        r'management[\'|\u2019]?s?\s+discussion\s+and\s+analysis\s+of\s+financial\s+condition',
    ]

    MDA_10Q_PATTERNS = [
        r'item\s*2[.\s]*management[\'|\u2019]?s?\s+discussion\s+and\s+analysis',
        r'item\s*2[.\s]*md&a',
        r'management[\'|\u2019]?s?\s+discussion\s+and\s+analysis',
    ]

    def parse_filing(self, html_content: str, form_type: str) -> dict:
        """
        Parse an SEC filing and extract all financial components.

        Args:
            html_content: Raw HTML content of the filing
            form_type: Type of filing (10-K, 10-Q, etc.)

        Returns:
            Dictionary containing extracted financial statements and MD&A
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        return {
            'income_statement': self.extract_income_statement(soup),
            'balance_sheet': self.extract_balance_sheet(soup),
            'cash_flow': self.extract_cash_flow(soup),
            'shareholders_equity': self.extract_shareholders_equity(soup),
            'retained_earnings': self.extract_retained_earnings(soup),
            'mda': self.extract_mda_section(soup, form_type),
        }

    def _is_financial_data_table(self, table) -> bool:
        """Check if a table contains actual financial data (not TOC or text snippet)."""
        text = table.get_text()

        # Must contain dollar amounts or numbers in parentheses (negative values)
        has_dollar = bool(re.search(r'\$\s*[\d,]+', text))
        has_parens_numbers = bool(re.search(r'\([\d,]+\)', text))

        # Count data rows (rows with numeric content - at least 3 digits)
        rows = table.find_all('tr')
        numeric_rows = sum(1 for r in rows if re.search(r'[\d,]{3,}', r.get_text()))

        # Financial tables should have dollar signs or parenthetical numbers AND multiple numeric rows
        return (has_dollar or has_parens_numbers) and numeric_rows >= 5

    def _is_toc_or_index_entry(self, element) -> bool:
        """Check if an element looks like a Table of Contents or index entry."""
        text = element.get_text(strip=True)

        # TOC entries often have page numbers at the end with dots/spaces leading to number
        # e.g., "Consolidated Balance Sheets...39" or "Balance Sheet    F-5"
        if re.search(r'\.{2,}\s*\d{1,3}\s*$', text):
            return True

        # Check for patterns like "F-5" at the end (page references in financial sections)
        if re.search(r'\s+F-\d{1,3}\s*$', text):
            return True

        # Very short text ending with just a page number (with leading spaces/dots)
        if len(text) < 80 and re.search(r'[\s.]+\d{1,3}\s*$', text):
            return True

        # Check if parent/ancestor is in a TOC section
        for parent in element.parents:
            if parent.name:
                parent_text = parent.get('id', '') + ' ' + parent.get('class', [''])[0] if parent.get('class') else parent.get('id', '')
                if 'toc' in parent_text.lower() or 'contents' in parent_text.lower():
                    return True

        return False

    def _score_table(self, table, element_position: int = 0) -> int:
        """Score a table by how likely it is to be a real financial data table."""
        score = 0
        text = table.get_text()
        rows = table.find_all('tr')

        # More rows = higher score
        score += len(rows) * 2

        # Count cells with dollar amounts
        dollar_matches = len(re.findall(r'\$\s*[\d,]+', text))
        score += dollar_matches * 3

        # Count cells with parenthetical numbers (negative values)
        paren_matches = len(re.findall(r'\([\d,]+\)', text))
        score += paren_matches * 3

        # Bonus for having multiple columns with numbers
        for row in rows[:10]:  # Sample first 10 rows
            cells = row.find_all(['td', 'th'])
            numeric_cells = sum(1 for c in cells if re.search(r'[\d,]{3,}', c.get_text()))
            if numeric_cells >= 2:
                score += 5

        # Bonus for tables appearing later in document (more likely to be in Item 8)
        # Tables in TOC are usually early, actual financial statements are later
        score += element_position // 10

        # Penalty if table appears to be in a TOC-like context
        for parent in table.parents:
            if parent.name:
                parent_id = parent.get('id', '').lower()
                parent_class = ' '.join(parent.get('class', [])).lower() if parent.get('class') else ''
                if 'toc' in parent_id or 'toc' in parent_class or 'contents' in parent_id:
                    score -= 100
                    break

        return score

    def _find_table_by_patterns(self, soup: BeautifulSoup, patterns: list) -> Optional[dict]:
        """
        Find the best matching table (not just first match).

        Returns dict with 'title', 'headers', 'rows', and 'html' keys.
        """
        candidates = []

        # Look for tables with matching captions or preceding headers
        all_text_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'b', 'strong', 'font'])

        for idx, element in enumerate(all_text_elements):
            text = element.get_text(strip=True).lower()

            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Skip if this looks like a TOC entry
                    if self._is_toc_or_index_entry(element):
                        continue

                    # Found a matching header, look for the next table
                    table = self._find_next_table(element)
                    if table and self._is_financial_data_table(table):
                        score = self._score_table(table, idx)
                        candidates.append((table, element.get_text(strip=True), score))

        # Also check table captions directly
        all_tables = soup.find_all('table')
        for idx, table in enumerate(all_tables):
            caption = table.find('caption')
            if caption:
                caption_text = caption.get_text(strip=True).lower()
                for pattern in patterns:
                    if re.search(pattern, caption_text, re.IGNORECASE):
                        if self._is_financial_data_table(table):
                            score = self._score_table(table, idx * 10)
                            candidates.append((table, caption.get_text(strip=True), score))

            # Check first row for header patterns
            first_row = table.find('tr')
            if first_row:
                row_text = first_row.get_text(strip=True).lower()
                for pattern in patterns:
                    if re.search(pattern, row_text, re.IGNORECASE):
                        if self._is_financial_data_table(table):
                            score = self._score_table(table, idx * 10)
                            candidates.append((table, first_row.get_text(strip=True)[:100], score))

        # Return the highest-scored candidate
        if candidates:
            best = max(candidates, key=lambda x: x[2])
            return self._parse_table(best[0], best[1])

        return None

    def _find_next_table(self, element) -> Optional[BeautifulSoup]:
        """Find the next table element after the given element."""
        # Check siblings
        for sibling in element.find_next_siblings():
            if sibling.name == 'table':
                return sibling
            # Check if sibling contains a table
            table = sibling.find('table')
            if table:
                return table

        # Check parent's next siblings
        parent = element.parent
        if parent:
            for sibling in parent.find_next_siblings():
                if sibling.name == 'table':
                    return sibling
                table = sibling.find('table')
                if table:
                    return table

        return None

    def _parse_table(self, table: BeautifulSoup, title: str = '') -> dict:
        """
        Parse an HTML table into a structured dictionary.

        Returns dict with title, headers, rows, and cleaned HTML.
        """
        rows = table.find_all('tr')
        parsed_rows = []
        headers = []

        for i, row in enumerate(rows):
            cells = row.find_all(['th', 'td'])
            cell_data = []

            for cell in cells:
                # Get text content, preserving some structure
                text = cell.get_text(separator=' ', strip=True)
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text)
                cell_data.append({
                    'text': text,
                    'is_header': cell.name == 'th',
                    'colspan': int(cell.get('colspan', 1)),
                    'rowspan': int(cell.get('rowspan', 1)),
                })

            if cell_data:
                # Check if this looks like a header row
                is_header_row = all(c['is_header'] for c in cell_data) or (
                    i == 0 and any(self._looks_like_header(c['text']) for c in cell_data)
                )

                if is_header_row and not headers:
                    headers = [c['text'] for c in cell_data]
                else:
                    parsed_rows.append([c['text'] for c in cell_data])

        # Generate clean, readable HTML for display
        cleaned_html = self._build_clean_financial_table(headers, parsed_rows)

        return {
            'title': title,
            'headers': headers,
            'rows': parsed_rows,
            'html': cleaned_html,
            'found': True,
        }

    def _looks_like_header(self, text: str) -> bool:
        """Check if text looks like a column header."""
        header_keywords = [
            'year', 'quarter', 'month', 'period', 'ended', 'weeks',
            'fiscal', 'december', 'january', 'february', 'march',
            'april', 'may', 'june', 'july', 'august', 'september',
            'october', 'november', 'total', 'amount'
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in header_keywords)

    def _clean_table_html(self, table: BeautifulSoup) -> str:
        """Clean table HTML for display, removing inline styles but keeping structure."""
        # Create a copy to modify
        import copy
        table_copy = copy.copy(table)

        # Remove most inline styles but keep basic structure
        for tag in table_copy.find_all(True):
            # Keep colspan and rowspan
            allowed_attrs = ['colspan', 'rowspan']
            attrs_to_keep = {k: v for k, v in tag.attrs.items() if k in allowed_attrs}
            tag.attrs = attrs_to_keep

        return str(table_copy)

    def _build_clean_financial_table(self, headers: list, rows: list) -> str:
        """Build a clean, readable HTML table from parsed financial data."""
        if not rows:
            return ''

        # Extract label and numeric values from each row
        # This handles misaligned columns from colspan in original HTML
        cleaned_rows = []
        header_values = []

        for row in rows:
            label = ''
            values = []

            for cell in row:
                cell_str = str(cell).strip()
                if not cell_str or cell_str in ['$', '—', '-']:
                    continue

                # Check if it looks like a number (with optional parentheses, commas)
                is_numeric = bool(re.match(r'^[\(\$\s]*[\d,]+\.?\d*[\)\s]*$', cell_str.replace(' ', '')))

                if is_numeric:
                    values.append(cell_str)
                elif not label:
                    label = cell_str
                elif not values:
                    # Could be a header/period description
                    values.append(cell_str)

            if label or values:
                cleaned_rows.append((label, values))
                # Track max number of value columns
                if len(values) > len(header_values):
                    header_values = values

        # Determine number of value columns from data rows with most values
        num_value_cols = 0
        for label, values in cleaned_rows:
            if label and values:  # Data rows (not header rows)
                num_value_cols = max(num_value_cols, len(values))

        html = ['<table class="financial-table">']
        html.append('<tbody>')

        for label, values in cleaned_rows:
            # Skip empty rows
            if not label and not values:
                continue

            html.append('<tr>')
            html.append(f'<th>{label}</th>')

            # Pad values to consistent column count
            for i in range(num_value_cols):
                val = values[i] if i < len(values) else ''
                html.append(f'<td>{val}</td>')

            html.append('</tr>')

        html.append('</tbody></table>')
        return '\n'.join(html)

    def extract_income_statement(self, soup: BeautifulSoup) -> dict:
        """Extract income statement / statement of operations."""
        result = self._find_table_by_patterns(soup, self.INCOME_STATEMENT_PATTERNS)
        if result:
            return result
        return {'found': False, 'title': 'Income Statement', 'headers': [], 'rows': [], 'html': ''}

    def extract_balance_sheet(self, soup: BeautifulSoup) -> dict:
        """Extract balance sheet / statement of financial position."""
        result = self._find_table_by_patterns(soup, self.BALANCE_SHEET_PATTERNS)
        if result:
            return result
        return {'found': False, 'title': 'Balance Sheet', 'headers': [], 'rows': [], 'html': ''}

    def extract_cash_flow(self, soup: BeautifulSoup) -> dict:
        """Extract cash flow statement."""
        result = self._find_table_by_patterns(soup, self.CASH_FLOW_PATTERNS)
        if result:
            return result
        return {'found': False, 'title': 'Cash Flow Statement', 'headers': [], 'rows': [], 'html': ''}

    def extract_shareholders_equity(self, soup: BeautifulSoup) -> dict:
        """Extract shareholders' equity statement."""
        result = self._find_table_by_patterns(soup, self.EQUITY_PATTERNS)
        if result:
            return result
        return {'found': False, 'title': "Shareholders' Equity", 'headers': [], 'rows': [], 'html': ''}

    def extract_retained_earnings(self, soup: BeautifulSoup) -> dict:
        """Extract retained earnings from Stockholders' Equity statement."""
        # First try standalone table (rare in modern filings)
        result = self._find_table_by_patterns(soup, self.RETAINED_EARNINGS_PATTERNS)
        if result and self._is_retained_earnings_table(result):
            return result

        # Extract from Stockholders' Equity statement
        equity_table = self._find_table_by_patterns(soup, self.EQUITY_PATTERNS)
        if equity_table and equity_table.get('found'):
            retained_section = self._extract_retained_earnings_section(equity_table)
            if retained_section:
                return retained_section

        return {'found': False, 'title': 'Retained Earnings', 'headers': [], 'rows': [], 'html': ''}

    def _is_retained_earnings_table(self, table_data: dict) -> bool:
        """Check if a table actually contains retained earnings statement data."""
        if not table_data or not table_data.get('found'):
            return False

        rows = table_data.get('rows', [])
        if len(rows) < 3:
            return False

        # Combine all row text for checking
        all_text = ' '.join(' '.join(str(cell) for cell in row) for row in rows).lower()

        # Must have key retained earnings line items
        required_patterns = [
            r'balance\s+(at\s+)?(beginning|end)',  # Beginning/ending balance
            r'(net\s+(income|earnings)|dividends)',  # Net income or dividends
        ]

        matches = sum(1 for p in required_patterns if re.search(p, all_text))
        return matches >= 2

    def _extract_retained_earnings_section(self, equity_data: dict) -> Optional[dict]:
        """Extract retained earnings section from stockholders' equity table."""
        rows = equity_data.get('rows', [])
        headers = equity_data.get('headers', [])

        # Method 1: Row-based section (10-K format with "Retained Earnings:" header)
        retained_rows = []
        in_retained_section = False

        for row in rows:
            row_text = ' '.join(str(cell) for cell in row).lower()

            # Start capturing at "Retained Earnings:" header
            if 'retained earnings' in row_text and ':' in row_text and not in_retained_section:
                in_retained_section = True
                continue

            # Stop at next major section
            if in_retained_section:
                if any(section in row_text for section in
                       ['accumulated other', 'treasury stock', 'total stockholders',
                        'total shareholders', 'common stock', 'additional paid']):
                    break
                if row and any(str(cell).strip() for cell in row):
                    retained_rows.append(row)

        if retained_rows:
            return {
                'found': True,
                'title': 'Statement of Retained Earnings',
                'headers': headers,
                'rows': retained_rows,
                'html': self._build_retained_earnings_html(headers, retained_rows),
            }

        # Method 2: Column-based extraction (10-Q format with "Retained Earnings" column)
        return self._extract_retained_earnings_column(equity_data)

    def _extract_retained_earnings_column(self, equity_data: dict) -> Optional[dict]:
        """Extract retained earnings activity from equity statement (10-Q columnar format)."""
        rows = equity_data.get('rows', [])

        # Strategy: Find the column with large balance values (>50000) for RE balances
        # and find activity values (income/dividends) from those specific rows

        # Step 1: Find the balance column by looking for large numbers in "Balances" rows
        balance_col_idx = None
        for row in rows:
            label = str(row[0]).lower() if row else ''
            if 'balances as of' in label:
                for idx, cell in enumerate(row):
                    cell_str = str(cell).replace(',', '').replace('$', '').replace(' ', '')
                    if cell_str.isdigit() and int(cell_str) > 50000:
                        balance_col_idx = idx
                        break
                if balance_col_idx:
                    break

        if balance_col_idx is None:
            return None

        # Step 2: Extract retained earnings activity
        extracted_rows = []
        for row in rows:
            if not row:
                continue

            row_label = str(row[0]).strip()
            row_label_lower = row_label.lower()

            # Skip empty or header rows
            if not row_label or 'amounts in millions' in row_label_lower:
                continue

            # For balance rows, use the balance column
            if 'balances as of' in row_label_lower:
                if len(row) > balance_col_idx:
                    val = str(row[balance_col_idx]).strip()
                    if val and val not in ['—', '-', '$', '']:
                        extracted_rows.append([row_label, val])

            # For income/dividend rows, find any significant numeric value
            elif any(term in row_label_lower for term in [
                'consolidated net income', 'net income', 'net earnings',
                'dividends declared', 'cash dividends'
            ]):
                # Find the first significant value that could affect RE
                for cell in row[1:]:
                    cell_str = str(cell).strip()
                    if cell_str in ['—', '-', '$', '']:
                        continue
                    cleaned = cell_str.replace(',', '').replace('(', '').replace(')', '').replace(' ', '').replace('$', '')
                    if cleaned.isdigit() and int(cleaned) > 100:
                        extracted_rows.append([row_label, cell_str])
                        break

        # Need at least balance rows and some activity
        if len(extracted_rows) >= 3:
            return {
                'found': True,
                'title': 'Retained Earnings Activity',
                'headers': ['Description', 'Amount (millions)'],
                'rows': extracted_rows,
                'html': self._build_retained_earnings_html(['Description', 'Amount (millions)'], extracted_rows),
            }
        return None

    def _build_retained_earnings_html(self, headers: list, rows: list) -> str:
        """Build HTML table for retained earnings statement."""
        html = ['<table class="financial-table">']

        if headers:
            html.append('<thead><tr>')
            html.append('<th>Description</th>')
            for h in headers[1:]:  # Skip first empty column header
                html.append(f'<th>{h}</th>')
            html.append('</tr></thead>')

        html.append('<tbody>')
        for row in rows:
            html.append('<tr>')
            for i, cell in enumerate(row):
                tag = 'th' if i == 0 else 'td'
                html.append(f'<{tag}>{cell}</{tag}>')
            html.append('</tr>')
        html.append('</tbody></table>')

        return '\n'.join(html)

    def extract_mda_section(self, soup: BeautifulSoup, form_type: str) -> dict:
        """
        Extract Management Discussion & Analysis section.

        Args:
            soup: BeautifulSoup object of the filing
            form_type: Filing type (10-K uses Item 7, 10-Q uses Item 2)

        Returns:
            Dictionary with 'found', 'title', 'content', and 'html' keys
        """
        patterns = self.MDA_10K_PATTERNS if '10-K' in form_type.upper() else self.MDA_10Q_PATTERNS
        end_patterns = [
            r'item\s*7a',  # Quantitative disclosures (10-K)
            r'item\s*8',   # Financial statements (10-K)
            r'item\s*3',   # Quantitative disclosures (10-Q)
            r'item\s*4',   # Controls (10-Q)
        ]

        # Find MD&A section start - skip TOC entries
        mda_start = None
        mda_candidates = []

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div', 'b', 'strong', 'font', 'a']):
            text = element.get_text(strip=True)
            text_lower = text.lower()
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    # Skip TOC entries (short text with page numbers)
                    if self._is_toc_or_index_entry(element):
                        continue
                    # Skip if it's just a link/anchor
                    if element.name == 'a' and len(text) < 100:
                        continue
                    mda_candidates.append(element)
                    break

        # Use the first non-TOC candidate, or look for the one with substantial following content
        for candidate in mda_candidates:
            # Check if there's actual content after this element
            next_elem = candidate.find_next(['p', 'div'])
            if next_elem:
                next_text = next_elem.get_text(strip=True)
                if len(next_text) > 50:  # Has substantial following content
                    mda_start = candidate
                    break

        if not mda_start and mda_candidates:
            mda_start = mda_candidates[0]

        if not mda_start:
            return {
                'found': False,
                'title': "Management's Discussion and Analysis",
                'content': '',
                'html': '',
            }

        # Collect content until next major section
        content_elements = []
        seen_elements = set()

        # Get text and HTML content by traversing siblings and their children
        max_elements = 1000  # Increased limit
        element_count = 0

        # Start from the parent container if mda_start is deeply nested
        start_container = mda_start.parent
        while start_container and start_container.name in ['b', 'strong', 'font', 'span', 'a']:
            start_container = start_container.parent

        current = start_container if start_container else mda_start

        for sibling in current.find_next_siblings():
            if element_count >= max_elements:
                break

            sibling_text = sibling.get_text(strip=True).lower()

            # Check if we've hit the next section
            hit_end = False
            for end_pattern in end_patterns:
                if re.search(end_pattern, sibling_text, re.IGNORECASE):
                    # Make sure it's a heading, not just a reference
                    if sibling.name in ['h1', 'h2', 'h3', 'h4', 'p', 'div']:
                        # Check if it starts with the pattern (actual section header)
                        if re.match(end_pattern, sibling_text[:50], re.IGNORECASE):
                            hit_end = True
                            break
            if hit_end:
                break

            # Collect paragraphs and divs with text content
            if sibling.name in ['p', 'div']:
                text = sibling.get_text(strip=True)
                if text and len(text) > 30 and id(sibling) not in seen_elements:
                    content_elements.append(sibling)
                    seen_elements.add(id(sibling))
                    element_count += 1
            elif sibling.name == 'table':
                # Include tables in MD&A
                if id(sibling) not in seen_elements:
                    content_elements.append(sibling)
                    seen_elements.add(id(sibling))
                    element_count += 1
            else:
                # Check for nested paragraphs
                for p in sibling.find_all(['p', 'div'], recursive=True):
                    text = p.get_text(strip=True)
                    if text and len(text) > 30 and id(p) not in seen_elements:
                        content_elements.append(p)
                        seen_elements.add(id(p))
                        element_count += 1
                        if element_count >= max_elements:
                            break

        # If we didn't find content via siblings, try find_next approach
        if not content_elements or len(content_elements) < 5:
            current = mda_start
            for _ in range(max_elements):
                current = current.find_next(['p', 'div', 'table'])
                if not current:
                    break

                current_text = current.get_text(strip=True).lower()

                # Check if we've hit the next section
                hit_end = False
                for end_pattern in end_patterns:
                    if re.match(end_pattern, current_text[:50], re.IGNORECASE):
                        hit_end = True
                        break
                if hit_end:
                    break

                text = current.get_text(strip=True)
                # Skip very short fragments and TOC-like entries
                if text and len(text) > 30 and id(current) not in seen_elements:
                    # Skip if it looks like a TOC entry
                    if not self._is_toc_or_index_entry(current):
                        content_elements.append(current)
                        seen_elements.add(id(current))

        # Build content
        text_content = []
        html_content = []

        for elem in content_elements[:100]:  # Limit output size
            text = elem.get_text(strip=True)
            if text and len(text) > 20:  # Skip very short fragments
                text_content.append(text)
                html_content.append(str(elem))

        return {
            'found': bool(text_content),
            'title': "Management's Discussion and Analysis",
            'content': '\n\n'.join(text_content[:50]),  # Limit paragraphs
            'html': '\n'.join(html_content[:50]),
        }
