# Soukchay API

A FastAPI-based read-only API for the soukchay_sysdata database, designed to serve the mobile Soukchay App.

## Features

- **Read-only access** to soukchay_sysdata database
- **UTF-8 support** for Lao text
- **5 main endpoints** covering all business areas:
  - Workers (data_entry + joined data)
  - Labor Department (Korea placement)
  - Loan Department (loans with computed interest)
  - FA Department (payments with computed fields)
  - Labor Follow-up (post-placement tracking)
- **Statistics endpoints** for all areas
- **Notification filtering** for health/visa/return reminders
- **API key authentication**
- **CORS support**

## Endpoints

### Workers
- `GET /workers` - List all workers with joined data
- `GET /workers/{cid}` - Get single worker by CID
- `GET /workers/stats` - Get worker statistics by status
- `GET /workers/{cid}/payments` - Get payment history for worker
- `GET /workers?status=X` - Filter by status
- `GET /workers?notify=heal|visa|departure|return` - Filter by notification type

### Labor Department
- `GET /labor-department` - List all labor department records
- `GET /labor-department/{id}` - Get single labor department record
- `GET /labor-department/stats` - Get labor department statistics

### Loan Department
- `GET /loan-department` - List all loan department records
- `GET /loan-department/{id}` - Get single loan department record
- Includes computed fields: days overdue, elapsed term days, interest payable

### FA Department
- `GET /fa-department` - List all FA department records
- `GET /fa-department/{id}` - Get single FA department record
- `GET /fa-department/{id}/payments` - Get payment history
- Includes computed fields: days overdue, interest payable, currency conversions

### Labor Follow-up
- `GET /follow-up` - List all labor follow-up records
- `GET /follow-up/{id}` - Get single labor follow-up record
- `GET /follow-up/stats` - Get labor follow-up statistics

### General
- `GET /health` - Health check endpoint
- `GET /docs` - API documentation
- `GET /redoc` - ReDoc documentation

## Setup

### Local Development

1. Install dependencies:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. Copy and configure `.env`:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. Start the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Test the API:
   ```bash
   python test_api.py
   ```

### Deployment to apis.com.la

1. Configure `.env` with production database credentials
2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```
3. The script will:
   - Upload the code to the server
   - Install dependencies
   - Create a systemd service
   - Configure Apache proxy
   - Set up SSL certificate
   - Start the service

## Database Schema

The API connects to the `soukchay_sysdata` database with the following main tables:

- `data_entry` - Worker records (31 columns)
- `labor_department` - Labor department records
- `labor_department_korea` - Korean placement details
- `loan_department` - Loan records with computed fields
- `fa_department` - Financial assistance records
- `labor_follow_korea` - Post-placement follow-up
- Supporting tables for provinces, districts, villages, employers, etc.

## Authentication

The API uses simple API key authentication. Add the header:
```
X-API-Key: your-api-key
```

## CORS

Configure CORS origins in `.env`:
```
CORS_ORIGINS=http://yourdomain.com,https://yourdomain.com
```

## Computed Fields

### Loan/FA Department
- `days_overdue` - Days since final due date
- `elapsed_term_days` - Days since first due date
- `interest_payable` - Simple interest calculation
- `over_under_amount` - Amount paid over/under total debt
- `total_debt_lak`/`total_debt_usd` - Currency conversions

## Testing

Run the test script:
```bash
python test_api.py
```

This will test the health check, workers endpoint, and stats endpoint.

## License

Internal project for Soukchay mobile app.