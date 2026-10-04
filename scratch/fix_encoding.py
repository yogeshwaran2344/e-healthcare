import os
import re

def fix_file(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'rb') as f:
        content = f.read()

    # UTF-8 encoded sequences of mojibake
    # â‚¹ in utf-8 is b'\xc3\xa2\xe2\x80\x9a\xc2\xb9'
    # â€¢ is b'\xc3\xa2\xe2\x82\xac\xc2\xa2'
    # â€” is b'\xc3\xa2\xe2\x82\xac\xe2\x80\x94'
    # âœ“ is b'\xc3\xa2\xc5\x93\xe2\x80\x9c'
    # â„ž is b'\xc3\xa2\xe2\x80\x9e\xc5\xbe'
    # Â· is b'\xc3\x82\xc2\xb7'

    text = content.decode('utf-8', errors='ignore')
    
    replacements = {
        'â‚¹': '₹',
        'â€¢': '•',
        'â€”': '—',
        'âœ“': '✓',
        'â„ž': '℞',
        'âš ï¸': '⚠️',
        'âš ': '⚠️',
        'â”œâ”€â”€': '├──',
        'â””â”€â”€': '└──',
        'Â·': '·',
        'â‚¬': '€'
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Fixed encoding in {filepath}")

fix_file('frontend/js/patient.js')
fix_file('frontend/patient.html')
