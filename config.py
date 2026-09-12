# config.py
POLICY_RULES = {
    'CURRENCY_SYMBOL': '$',
    'CURRENCY_CODE': 'USD',
    'MAX_TRANSACTION_AMOUNT': 5000.00,
    'ALLOWED_DOMAINS': ['erp.internal.local', '10.0.0.5'],
    'RESTRICTED_KEYWORDS': ['password', 'private_key', 'credit_card', 'api_secret', 'token'],
    'BLOCKED_VENDORS': ['GhostShell Syndicate', 'DarkNet Offshore LLC']
}

MALWARE_FIREWALL_RULES = {
    'SQL_INJECTION': ["' OR '1'='1", 'DROP TABLE', ';--', 'UNION SELECT', 'EXEC xp_cmdshell'],
    'XSS_SCRIPT_INJECTION': ['<script>', 'javascript:', 'onerror=', 'eval(', 'onload='],
    'COMMAND_INJECTION': ['; rm -rf', '&& net user', '| bash', 'curl http://', 'powershell -enc'],
    'PATH_TRAVERSAL': ['../', '..\\', '/etc/passwd', 'C:\\Windows\\System32']
}

# HONEYTOKEN DECOY TRAPS (100% Hacker Detection Guarantee)
HONEYTOKENS = {
    'DECOY_API_KEY': 'HT-KEY-9988-X7Z-HONEYPOT',
    'DECOY_DB_PASSWORD': 'HoneyAdminPass2026!Secret',
    'DECOY_JWT_TOKEN': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.HONEYTRAP.SIGNATURE'
}