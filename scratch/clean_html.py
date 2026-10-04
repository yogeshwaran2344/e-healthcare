import re

with open('frontend/patient.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Normalize double newlines if any
text = re.sub(r'\n{3,}', '\n\n', text)

# Add Test Live WhatsApp Ping button in the presets row
target_btn = '<button type="button" class="btn btn-outline-secondary btn-sm" onclick="setQuickManualVitals(120, 80, 76, 98)">'
replacement_btn = """<button type="button" class="btn btn-outline-secondary btn-sm" onclick="setQuickManualVitals(120, 80, 76, 98)">"""

test_btn_code = """
                                        <button type="button" class="btn btn-outline-success btn-sm fw-semibold" onclick="testLiveWhatsAppPing()">
                                            <i class="bi bi-whatsapp me-1"></i> Test Live WhatsApp Ping
                                        </button>"""

if 'Test Live WhatsApp Ping' not in text:
    text = text.replace('Preset: Normal 120/80\n                                        </button>', 'Preset: Normal 120/80\n                                        </button>' + test_btn_code)

with open('frontend/patient.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Formatted patient.html and ensured test button is present")
