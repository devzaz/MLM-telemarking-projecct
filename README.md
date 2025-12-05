# 📞 MLM Telemarketing CRM + Referral Tracking + Commission Engine

A full-stack Django-based Telemarketing & MLM CRM application with:

- Multi-role authentication (Admin, Telemarketer, Affiliate, Customer)
- Referral tracking system with long-lived cookies (30–180 days)
- Automated commission engine (direct + binary MLM matching)
- Telemarketing CRM (leads, calling workflow, statuses)
- Wallet & payout system
- REST API (JWT + API Keys)
- External order tracking and conversion recording
- Email verification system
- Admin dashboards & reporting

---

## 🚀 Features

### ✅ **User System**
- Custom Django user model with roles  
- Email verification on signup  
- Referral codes auto-generated per user  
- JWT authentication for API access  
- Role-based permissions

### 🎯 **Telemarketing CRM**
- Lead list, assignment, and status updates  
- Telemarketer dashboards  
- Lead conversion into sales  
- Automatic commission creation for telemarketers  

### 🔗 **Referral System**
- Tracks visitors through links like:  
- Referral cookie stored for 30–180 days  
- ReferralToken created on first visit  
- Conversion tracked through:
- Browser cookie  
- Referral token  
- Referral code  

### 💰 **Commission Engine**
- Direct commissions for telemarketers  
- MLM binary matching commission  
- Wallet system with:
- Credit transactions on commission approval  
- Debit transactions on payouts  
- Admin approval workflow  
- Automatic commission approval (optional)

### 🌐 **REST API**
Includes:

| Endpoint | Description |
|---------|-------------|
| `POST /api/token/` | Get JWT access token |
| `POST /api/referral/check/` | Validate a referral token |
| `POST /api/sale/verify/` | Record external conversion (referral) |
| `POST /commissions/api/record-sale/` | Record telemarketing sale |

Supports:
- JWT authentication
- API key authentication
- Shared secret authentication for legacy referral endpoints

### ✉️ **Email System**
- Registration email verification  
- Customizable email templates  
- SMTP support (Gmail, SendGrid, etc.)

---

## 🛠️ Tech Stack

- **Backend:** Django 5, Django REST Framework
- **DB:** SQLite (dev) / PostgreSQL (production)
- **Auth:** Django Auth, JWT (SimpleJWT), API Keys
- **Frontend:** Django Templates (Bootstrap)
- **Tasking / Pipelines:** Django signals
- **Deployment:** WSGI (Gunicorn/Nginx recommended)

---

## 📂 Project Structure

project/
│
├── config/ # Django project settings, URLs, WSGI
├── users/ # Custom user model, auth, verification
├── referrals/ # ReferralToken, ReferralConversion, middleware
├── crm/ # Leads, telemarketing workflow
├── telemarketing/ # Future telemarketing features
├── commissions/ # Commission engine, wallets, payouts
├── api/ # Public API endpoints
├── mlm/ # Binary MLM tree
├── templates/ # HTML templates
└── static/ # Static assets



---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository:

```bash
git clone https://github.com/devzaz/MLM-telemarking-projecct.git
cd MLM-telemarking-projecct


python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows


pip install -r requirements.txt


SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your@gmail.com
REFERRAL_SHARED_SECRET=CHANGE_THIS


python manage.py migrate

python manage.py runserver


POST /api/sale/verify/
{
  "external_order_id": "ORD-556",
  "referral_token": "aabbccddeeff0099",
  "amount": "59.00"
}


