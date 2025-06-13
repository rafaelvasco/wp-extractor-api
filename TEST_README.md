# HTML Utils Testing

This directory contains comprehensive tests for the HTML content cleaning utilities used in the WordPress Extractor API.

## Test Files

- `test_html_utils.py` - Focused test suite covering the main HTML entity issues
- `run_tests.py` - Simple test runner script
- `html_utils.py` - The module being tested

## Running Tests

### Option 1: Using the custom test runner

```bash
python3 run_tests.py
```

### Option 2: Using unittest directly

```bash
python3 -m unittest test_html_utils.py -v
```

### Option 3: Using pytest (if available)

```bash
pytest test_html_utils.py -v
```

## Test Coverage

The test suite covers:

### HTML Entity Decoding

- ✅ Em dash (`&#8211;` → `–`)
- ✅ En dash (`&#8212;` → `—`)
- ✅ Smart quotes (`&#8220;` → `"`, `&#8221;` → `"`)
- ✅ Apostrophes (`&#8217;` → `'`)
- ✅ Ampersand (`&#38;` → `&`)
- ✅ Less/greater than (`&#60;` → `<`, `&#62;` → `>`)
- ✅ Non-breaking space (`&#160;` → ` `)

### HTML Tag Removal

- ✅ Basic tags (`<p>`, `<div>`, `<h1>`, etc.)
- ✅ Nested tags
- ✅ Malformed HTML
- ✅ Mixed case tags

### Text Processing

- ✅ Whitespace normalization
- ✅ Portuguese accent preservation
- ✅ Special character handling
- ✅ Line break preservation (for `clean_html_content_with_linebreaks`)

### Real-World Scenarios

- ✅ WordPress content examples
- ✅ The original issue case: `"Art. 241 &#8211; B &#8211; Posse ou armazenamento de pornografia infantil"`
- ✅ Complex mixed content

### Edge Cases

- ✅ Empty strings
- ✅ Only entities
- ✅ Only HTML tags
- ✅ Malformed HTML

## Expected Test Results

All tests should pass. The main test case that was failing before the fix:

**Input:** `"Art. 241 &#8211; B &#8211; Posse ou armazenamento de pornografia infantil"`
**Expected:** `"Art. 241 – B – Posse ou armazenamento de pornografia infantil"`
**Previous (broken):** `"Art. 241  B  Posse ou armazenamento de pornografia infantil"`

## Test Structure

Each test method focuses on a specific aspect:

- `test_clean_html_content_basic_html_entities()` - Core entity decoding
- `test_clean_html_content_various_entities()` - Multiple entity types
- `test_clean_html_content_with_html_tags()` - HTML tag removal
- `test_clean_html_content_portuguese_accents()` - Portuguese character preservation
- `test_clean_html_content_whitespace_handling()` - Whitespace normalization
- `test_clean_html_content_with_linebreaks_*()` - Line break preservation tests
- `test_clean_html_content_edge_cases()` - Edge cases and error conditions
- `test_real_world_wordpress_content()` - Real WordPress content examples

## Dependencies

The tests use only Python standard library modules:

- `unittest` - Test framework
- `html_utils` - The module being tested

All external dependencies (BeautifulSoup4, etc.) are already included in `requirements.txt`.
