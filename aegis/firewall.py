# aegis/firewall.py
import re
import hashlib
import json
from datetime import datetime, timezone
import config

class AutonomousFirewall:
    def __init__(self):
        self.signatures = config.MALWARE_FIREWALL_RULES
        self.healing_logs = []

    def inspect_and_heal(self, payload: dict):
        sanitized_payload = json.loads(json.dumps(payload))
        detected_threats = []

        for field, value in payload.items():
            if isinstance(value, str):
                for threat_type, patterns in self.signatures.items():
                    for pattern in patterns:
                        if pattern.lower() in value.lower():
                            threat_id = 'THR-' + hashlib.sha256((field + pattern).encode()).hexdigest()[:8].upper()
                            match_idx = value.lower().find(pattern.lower())
                            pattern_regex = re.compile(re.escape(pattern), re.IGNORECASE)
                            cleaned_value = pattern_regex.sub('[NEUTRALIZED_MALWARE_STRING]', sanitized_payload[field])
                            sanitized_payload[field] = cleaned_value

                            healing_event = {
                                'threat_id': threat_id,
                                'threat_type': threat_type,
                                'infected_field': field,
                                'signature_matched': pattern,
                                'offset_index': match_idx,
                                'resolution': 'AUTONOMOUS_INLINE_SANITIZATION_SUCCESS',
                                'timestamp': datetime.now(timezone.utc).isoformat()
                            }
                            detected_threats.append(healing_event)
                            self.healing_logs.append(healing_event)

        return sanitized_payload, detected_threats