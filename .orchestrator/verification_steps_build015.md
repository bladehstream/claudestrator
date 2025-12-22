# BUILD-015: Email Notifications - Verification Steps

## Build Verification

### Syntax Check
```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator
python3 -m py_compile app/backend/services/email_notification_service.py
python3 -m py_compile app/backend/services/email_scheduler.py
python3 -m py_compile app/backend/services/vulnerability_hooks.py
python3 -m py_compile app/backend/api/admin_email.py
```

**Expected:** All files compile without syntax errors

### Imports Check
```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator
python3 -c "from app.backend.services.email_notification_service import EmailNotificationService; print('✓ Email service imported')"
python3 -c "from app.backend.services.email_scheduler import start_email_scheduler, stop_email_scheduler; print('✓ Email scheduler imported')"
python3 -c "from app.backend.api.admin_email import router; print('✓ Admin email router imported')"
```

**Expected:** All imports succeed

### Database Models Check
```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator
python3 -c "from app.database.models import SMTPConfig, EmailNotificationConfig, EmailAlert; print('✓ New models imported')"
```

**Expected:** New database models import without errors

## Runtime Verification

### Start Application
```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator
python3 app/main.py &
sleep 5
```

**Expected:** Application starts without errors, email scheduler initializes

### Health Check
```bash
curl -X GET http://localhost:8000/admin/email/health
```

**Expected Response:**
```json
{
  "smtp_configured": false,
  "smtp_verified": false,
  "notifications_enabled": false,
  "recipients_count": 0,
  "message": "SMTP not configured"
}
```

### Configure SMTP
```bash
curl -X POST http://localhost:8000/admin/email/smtp/config \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "alerts@example.com",
    "sender_name": "VulnDash Alerts",
    "smtp_username": "test@gmail.com",
    "smtp_password": "app-password"
  }'
```

**Expected:** Returns 201 with SMTP config

### Test SMTP Connection
```bash
curl -X POST http://localhost:8000/admin/email/smtp/test \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "test@gmail.com",
    "smtp_password": "app-password"
  }'
```

**Expected:** Either "success": true or clear error message

### Get SMTP Config
```bash
curl -X GET http://localhost:8000/admin/email/smtp/config
```

**Expected:** Returns SMTP configuration with sender details

### Configure Notifications
```bash
curl -X POST http://localhost:8000/admin/email/notification/config \
  -H "Content-Type: application/json" \
  -d '{
    "alert_on_kev": true,
    "alert_on_high_epss": true,
    "epss_threshold": 0.8,
    "recipient_emails": ["admin@example.com"],
    "digest_enabled": true,
    "digest_hours": 24,
    "is_enabled": false
  }'
```

**Expected:** Returns 201 with notification config

### Get Notification Config
```bash
curl -X GET http://localhost:8000/admin/email/notification/config
```

**Expected:** Returns notification configuration with recipients

### Health Check (After Configuration)
```bash
curl -X GET http://localhost:8000/admin/email/health
```

**Expected:** Shows configuration status

## Unit Tests

### Run Email Service Tests
```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator
python3 -m pytest tests/test_email_notification_service.py -v --tb=short
```

**Expected:** All tests pass (25+ tests)

### Run Email API Tests
```bash
python3 -m pytest tests/test_email_api.py -v --tb=short
```

**Expected:** All tests pass (15+ tests)

## Integration Test - Email Alert Queueing

### Verify Alert Queuing Logic
```bash
# This would be done in integration tests, but manually:
# 1. Create SMTP config
# 2. Create notification config with recipients
# 3. Create a Vulnerability with KEV status
# 4. Call email_service.queue_alerts_for_vulnerability()
# 5. Verify EmailAlert records created in database
```

**Expected:** EmailAlert records created for each alert type and recipient

## Database Verification

### Check New Tables Created
```bash
sqlite3 vulndash.db ".tables"
```

**Expected Output includes:**
- smtp_config
- email_notification_config
- email_alerts

### Check Table Schemas
```bash
sqlite3 vulndash.db ".schema smtp_config"
sqlite3 vulndash.db ".schema email_notification_config"
sqlite3 vulndash.db ".schema email_alerts"
```

**Expected:** Tables have all required columns

## Cleanup
```bash
# Kill running server
pkill -f "python3 app/main.py"
```

---

## Expected Outcomes

- [✓] Email service module compiles without errors
- [✓] Email scheduler module compiles without errors
- [✓] Admin email API router compiles without errors
- [✓] Vulnerability hooks module compiles without errors
- [✓] All new database models import successfully
- [✓] New database tables created (smtp_config, email_notification_config, email_alerts)
- [✓] Application starts with email scheduler initialized
- [✓] SMTP configuration endpoints respond correctly
- [✓] Email notification configuration endpoints respond correctly
- [✓] Health check endpoint returns correct status
- [✓] Email alert queuing works correctly
- [✓] Email service respects notification settings
- [✓] All unit tests pass (40+ tests)
