# SECTION C 

## Question 3

**Scenario:** 1000 internships published. Within 1 hour, 50,000 students apply.

The system will use **horizontal scaling** — multiple Django server instances running behind a **Load Balancer (Nginx)**. Each incoming request gets distributed across servers so no single server gets overloaded. Auto-scaling can be configured on cloud platforms (AWS/GCP) to spin up new instances when traffic spikes.

---

### 2. How will you prevent duplicate applications?

Two layers of protection are implemented:

**Database Level** — `unique_together` constraint on `(student, internship)` fields. Even if two simultaneous requests arrive, the database will reject the second one.

**Application Level** — Validation check in serializer before saving to DB:

```python
if Application.objects.filter(student=request.user, internship=value).exists():
    raise serializers.ValidationError("You have already applied for this internship.")
```

---

### 3. How will you keep response time below 500ms?

- **Redis Caching** — Frequently accessed data like internship listings are cached, reducing database hits.
- **Database Indexes** — Proper indexes on filtered/sorted columns speed up queries significantly.
- **select_related() / prefetch_related()** — Reduces N+1 query problems in Django ORM.
- **Pagination** — Instead of returning 50,000 records at once, data is returned page by page (e.g., 20 per page).
- **Gunicorn Workers** — Multiple worker processes to handle concurrent requests.

---

### 4. What indexes will you create?

```sql
-- Applications Table
CREATE INDEX idx_applications_internship_id ON applications(internship_id);
CREATE INDEX idx_applications_student_id ON applications(student_id);
CREATE INDEX idx_applications_created_at ON applications(applied_at DESC);

-- Composite Index for filtering + sorting together
CREATE INDEX idx_applications_internship_created ON applications(internship_id, applied_at DESC);

-- Internships Table
CREATE INDEX idx_internships_company_id ON internships(company_id);
CREATE INDEX idx_internships_created_at ON internships(created_at DESC);
```

---

### 5. Will you use Redis?

Yes. Redis will be used for:

- **Caching** — Cache internship list responses to avoid repeated DB queries.
- **Rate Limiting** — Prevent a single user from flooding the API with requests.
- **Session/Token Storage** — Fast access to authentication data.
- **Queue Broker** — Act as message broker for Celery task queue.

---

### 6. Will you use Queue Systems (RabbitMQ/Kafka)?

Yes. **Celery with Redis** as the message broker will be used.

When 50,000 students apply simultaneously, instead of writing directly to the database (which would cause overload), each application request is pushed to a **queue**. Celery workers process these jobs in the background at a controlled rate.

```
Student applies → API receives request → Push to Queue → Celery Worker → Save to Database → Send Email Notification
```

This ensures:
- API responds immediately (fast response to user)
- Database is not overwhelmed
- Email notifications are sent asynchronously

---

### 7. How will you scale the system?

| Layer | Scaling Strategy |
|-------|-----------------|
| API Layer | Multiple Django instances + Nginx Load Balancer |
| Database | PostgreSQL Primary + Read Replicas for heavy reads |
| Cache | Redis Cluster for distributed caching |
| Queue | Scale Celery workers horizontally based on load |
| Storage | AWS S3 or similar for file/media storage |
| Deployment | Docker + Kubernetes for container orchestration |

---

# SECTION D — QUERY OPTIMIZATION (10 Marks)

## Question 4

**Given Query:**
```sql
SELECT * FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC;
```
*(Table has more than 10 million records)*

---

### 1. Why is the query slow?

- **No index on `internship_id`** — The database performs a full table scan across all 10 million rows instead of directly jumping to matching records.
- **No index on `created_at`** — Sorting without an index requires loading all matched rows into memory and sorting them, which is expensive.
- **`SELECT *`** — Fetches all columns including unnecessary ones, increasing I/O and memory usage.
- **No LIMIT** — All matching rows are returned at once, which can be thousands of records.

---

### 2. How will you optimize it?

**Step 1 — Select only required columns:**
```sql
SELECT id, student_id, status, created_at
FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC;
```

**Step 2 — Add pagination:**
```sql
SELECT id, student_id, status, created_at
FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

**Step 3 — Create a composite index (most important):**
```sql
CREATE INDEX idx_applications_internship_created
ON applications(internship_id, created_at DESC);
```

---

### 3. What indexes will you create?

```sql
-- Composite index handles both WHERE filter and ORDER BY in one index
CREATE INDEX idx_applications_internship_created
ON applications(internship_id, created_at DESC);

-- Separate index for student-based queries
CREATE INDEX idx_applications_student_id
ON applications(student_id);
```

**In Django models.py:**
```python
class Meta:
    indexes = [
        models.Index(fields=['internship', '-applied_at']),
        models.Index(fields=['student']),
    ]
```

---

### 4. How will you measure performance improvement?

Use PostgreSQL's `EXPLAIN ANALYZE` command before and after adding the index:

```sql
EXPLAIN ANALYZE
SELECT id, student_id, status, created_at
FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC
LIMIT 20;
```

**Expected improvement:**

| Metric | Before Index | After Index |
|--------|-------------|-------------|
| Scan Type | Full Table Scan | Index Scan |
| Rows Scanned | 10,000,000 | ~500 |
| Query Time | ~2000ms | ~5–10ms |
| Cost | Very High | Very Low |

---

# SECTION E — SYSTEM DESIGN (10 Marks)

## Question 5 — Backend Architecture for Internship Management Platform

---

### Architecture Diagram

```
                        ┌──────────────────┐
                        │     CLIENT        │
                        │  (Web / Mobile)   │
                        └────────┬─────────┘
                                 │ HTTPS
                        ┌────────▼─────────┐
                        │     NGINX         │
                        │  Load Balancer    │
                        └────────┬─────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
      ┌────────▼──────┐ ┌────────▼──────┐ ┌────────▼──────┐
      │  Django App   │ │  Django App   │ │  Django App   │
      │  Instance 1   │ │  Instance 2   │ │  Instance 3   │
      └────────┬──────┘ └────────┬──────┘ └────────┬──────┘
               └─────────────────┼─────────────────┘
                                 │
               ┌─────────────────┼──────────────────┐
               │                                    │
      ┌────────▼──────────┐             ┌───────────▼────────┐
      │   CACHE LAYER     │             │   QUEUE LAYER       │
      │   Redis           │             │   Celery + Redis    │
      │  - Internships    │             │  - Apply jobs       │
      │  - Sessions       │             │  - Email tasks      │
      │  - Rate limiting  │             │  - Notifications    │
      └───────────────────┘             └───────────┬────────┘
                                                    │
               ┌────────────────────────────────────┘
               │
      ┌────────▼──────────┐         ┌────────────────────┐
      │  DATABASE LAYER   │         │  NOTIFICATION       │
      │  PostgreSQL       │         │  SERVICE            │
      │  Primary (Write)  │         │  - Email (SMTP)     │
      │  Replica (Read)   │         │  - Push (Firebase)  │
      └───────────────────┘         └────────────────────┘
```

---

### Layer-wise Explanation

**1. API Layer (Django REST Framework)**
- Handles all incoming HTTP requests
- JWT Authentication via `djangorestframework-simplejwt`
- Modules: Authentication, Internship Management, Application Management, Analytics

**2. Cache Layer (Redis)**
- Caches internship listings to reduce DB load
- Stores rate-limiting counters
- Acts as session store for fast token validation

**3. Queue Layer (Celery + Redis)**
- Processes heavy background tasks asynchronously
- Handles application submissions during traffic spikes
- Sends email and push notifications without blocking the API

**4. Database Layer (PostgreSQL)**
- Primary instance handles all write operations
- Read Replica handles heavy read queries (listing, analytics)
- Proper indexes ensure fast query performance

**5. Notification Service**
- Email notifications via SMTP (e.g., SendGrid / Gmail)
- Push notifications via Firebase Cloud Messaging (FCM)
- Triggered by Celery workers after application events

---

### Module Summary

| Module | Technology | Responsibility |
|--------|-----------|----------------|
| Authentication | JWT + Django Auth | Register, Login, Profile |
| Internship Management | Django ORM + PostgreSQL | CRUD for internships |
| Application Management | Celery Queue + PostgreSQL | Apply, list, status update |
| Notifications | Celery + SMTP/Firebase | Email & push alerts |
| Analytics Dashboard | PostgreSQL Aggregations + Redis | Stats and reports |

---

*Assessment — IQRAA Mark Pvt Ltd Backend Developer Technical Assessment*