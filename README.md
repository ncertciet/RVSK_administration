## Administration Ingestion API

FastAPI service for receiving school administration records from state ERP systems
and upserting them into PostgreSQL tables under the `administration` schema.

### Main Endpoint

```text
POST /api/v1/administration/ingest
```

The endpoint expects a JSON array of school records and requires a Bearer JWT.
The token is verified locally with `public.pem`, then checked against the
configured auth service at `/me`.

### Request Flow

1. Verify JWT signature.
2. Verify active user with the auth API.
3. Validate payload shape and field values.
4. Ensure all records belong to one state.
5. Ensure authenticated user state matches payload state.
6. Split each record into configured table-wise rows.
7. Bulk upsert rows into PostgreSQL in one transaction.

### Target Tables

- `administration.master_schools_location`
- `administration.school_enrollment_statistics`
- `administration.school_teacher_statistics`
- `administration.school_infrastructure`
- `administration.school_benefit_distribution`
- `administration.school_smc_details`

The conflict keys are configured in `app/config/table_schema.py`. PostgreSQL
must have matching unique indexes or primary keys. See
`deployment/postgres_constraints.sql`.

### Local Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production Configuration

Use environment variables or a secret manager. Do not commit `.env`.

Start from `.env.example` and set:

- `ENVIRONMENT=production`
- `DEBUG=False`
- `ENABLE_DOCS=False`
- `CORS_ALLOWED_ORIGINS=<trusted domains only>`
- database credentials from your deployment secret store
- `AUTH_BASE_URL` for the production authentication service

If `ENVIRONMENT=production`, the app refuses wildcard CORS (`*`).

### Health Checks

```text
GET /health
GET /ready
```

`/health` confirms the application process is alive.
`/ready` checks database connectivity and should be used by load balancers or
container orchestrators.

### Deployment Notes

Before going live:

1. Run `deployment/postgres_constraints.sql` on the target database.
2. Confirm `public.pem` matches the production auth service signing key.
3. Configure HTTPS at the reverse proxy or platform layer.
4. Set request body size limits at the proxy based on expected payload size.
5. Send application logs to your central logging platform.
6. Load test with realistic state payloads.
