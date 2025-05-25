# OCR-to-JSON Data Generation Taxonomy

## Purpose
Generate synthetic training data for converting noisy OCR text to structured JSON format.

## Data Structure
Each example should contain:
- **Input**: Noisy OCR text with typical OCR errors (typos, spacing issues, character recognition errors)
- **Output**: Clean, structured JSON with extracted fields

## Target Fields for ID Card Processing
- `name`: Person's full name
- `dob`: Date of birth in YYYY-MM-DD format  
- `id_number`: Identity card number
- `address`: Full address (optional)
- `nationality`: Nationality (optional)

## OCR Error Patterns to Include
1. Character substitution (0→O, 1→l, 5→S)
2. Missing spaces or extra spaces
3. Line breaks in wrong places
4. Partial text recognition
5. Reversed character order in some fields

## Example Format
Input: Messy OCR text like "Nam: Priya\nDat of Brith: 13/04/2002\nID no: 1234-5678-9101"
Output: {"name": "Priya", "dob": "2002-04-13", "id_number": "1234-5678-9101"}

## Variations to Generate
- Different name formats (first/last, with middle names)
- Various date formats (DD/MM/YYYY, MM-DD-YYYY, etc.)
- Different ID number patterns
- Multiple languages/scripts
- Various document types (ID cards, licenses, certificates)
