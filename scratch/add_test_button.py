with open('frontend/patient.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = """                                        </div>
                                    </div>
                                </div>

                                <div class="row g-3 mb-3">"""

replacement = """                                        </div>
                                    </div>
                                    <div class="mt-3 pt-2 border-top d-flex justify-content-between align-items-center flex-wrap gap-2">
                                        <small class="text-muted"><i class="bi bi-info-circle me-1"></i> Instant live carrier delivery test</small>
                                        <button type="button" class="btn btn-sm btn-outline-success fw-semibold" onclick="testLiveWhatsAppPing()">
                                            <i class="bi bi-whatsapp me-1"></i> Test Live WhatsApp Ping
                                        </button>
                                    </div>
                                </div>

                                <div class="row g-3 mb-3">"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open('frontend/patient.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully added button in patient.html')
else:
    print('Target not found in patient.html')

# Add testLiveWhatsAppPing to patient.js
with open('frontend/js/patient.js', 'r', encoding='utf-8') as f:
    js_text = f.read()

js_addition = """
async function testLiveWhatsAppPing() {
    const cfg = getContactSettings();
    const phone = document.getElementById('profCaretakerPhone')?.value || cfg.caretakerPhone || "+918618912755";
    
    showSMSNotification({
        title: "TRANSMITTING LIVE WHATSAPP PING...",
        message: `Contacting Twilio carrier gateway for ${phone}...`,
        channel: "whatsapp",
        duration: 4000
    });

    try {
        const res = await API.post('/api/closed-loop/caregiver/test-live-whatsapp', { phone });
        if (res.success) {
            alert(`✅ LIVE WHATSAPP MESSAGE SENT!\\n\\nTarget Phone: ${res.target_phone}\\nProvider: ${res.provider}\\n\\nCheck your WhatsApp inbox on ${res.target_phone} right now!`);
            showSMSNotification({
                title: "✅ LIVE WHATSAPP DELIVERED",
                message: `Live message confirmed delivered to ${res.target_phone} via ${res.provider}.`,
                channel: "whatsapp",
                duration: 10000
            });
        } else {
            const envCheck = res.twilio_env_check || {};
            alert(`⚠️ Live Dispatch Diagnostic Report:\\n\\nTarget Phone: ${res.target_phone}\\nProvider: ${res.provider}\\nError / Carrier Status: ${res.error_details || 'Carrier refused'}\\n\\nServer Credentials Check:\\n- TWILIO_ACCOUNT_SID configured on Render: ${envCheck.TWILIO_ACCOUNT_SID_SET ? 'YES' : 'NO'}\\n- TWILIO_AUTH_TOKEN configured on Render: ${envCheck.TWILIO_AUTH_TOKEN_SET ? 'YES' : 'NO'}\\n- TWILIO_WHATSAPP_FROM: ${envCheck.TWILIO_WHATSAPP_FROM || 'Not set'}`);
        }
    } catch (err) {
        alert("Carrier test request failed: " + err.message);
    }
}
"""

if 'testLiveWhatsAppPing' not in js_text:
    js_text += "\n" + js_addition
    with open('frontend/js/patient.js', 'w', encoding='utf-8') as f:
        f.write(js_text)
    print('Successfully added testLiveWhatsAppPing to patient.js')
