import re

with open('frontend/patient.html', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'(id=["\']profCaretakerRelation["\'].*?</select>\s*</div>\s*</div>\s*)(</div>)'
btn_html = r"""\1    <div class="mt-3 pt-2 border-top d-flex justify-content-between align-items-center flex-wrap gap-2">
                                        <small class="text-muted"><i class="bi bi-info-circle me-1"></i> Instant live carrier delivery test</small>
                                        <button type="button" class="btn btn-sm btn-outline-success fw-semibold" onclick="testLiveWhatsAppPing()">
                                            <i class="bi bi-whatsapp me-1"></i> Test Live WhatsApp Ping
                                        </button>
                                    </div>
                                \2"""

new_text, count = re.subn(pattern, btn_html, text, flags=re.DOTALL)
print(f"Substitutions made: {count}")
if count > 0:
    with open('frontend/patient.html', 'w', encoding='utf-8') as f:
        f.write(new_text)
