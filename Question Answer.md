# SECTION C 

### 1. How will your system handle this traffic?

The system will use horizontal scaling, meaning multiple Django server instances will run at the same time behind an Nginx Load Balancer. When a large number of requests come in, the load balancer distributes them evenly across all server instances so no single server gets overwhelmed. If traffic increases further, new server instances can be automatically added using cloud platforms like AWS or GCP.

---

### 2. How will you prevent duplicate applications?

Two layers of protection are used to prevent this.

At the database level, a unique constraint is placed on the student and internship fields together. This means the database itself will reject any duplicate entry, even if two requests arrive at the exact same time.

At the application level, a validation check runs inside the serializer before anything is saved to the database. If the student has already applied for that internship, the system immediately returns an error without touching the database at all.

Both layers working together make it impossible for a student to apply twice for the same internship.


### 3. How will you keep response time below 500ms?

First, Redis caching is used so that frequently requested data like the internship list does not hit the database every time. The response is served directly from cache, which is much faster.

Second, proper database indexes are created on the columns that are most commonly used in filters and sorting. Without indexes, the database scans every single row, which is very slow when there are millions of records.

Third, Django's select_related and prefetch_related methods are used to avoid the N+1 query problem, where fetching 100 records would otherwise trigger 100 extra database queries.

Fourth, pagination is applied so that instead of returning thousands of records in one response, only 20 records are returned per page.

Fifth, Gunicorn is used with multiple worker processes so that many requests can be handled at the same time in parallel.


### 4. What indexes will you create?

Indexes will be created on the internship_id column, the student_id column, and the created_at column in the applications table. A composite index on both internship_id and created_at together is especially useful because it handles both the WHERE filter and the ORDER BY sorting in a single index lookup.

In the internships table, indexes will be created on the company_id and created_at columns.


### 5. Will you use Redis?

Yes. Redis will be used for four main purposes. First, for caching internship list responses so the database is not hit repeatedly. Second, for rate limiting so a single user cannot flood the API with too many requests. Third, for storing session and token data for fast access. Fourth, as the message broker for the Celery task queue.


### 6. Will you use Queue Systems?

Yes. Celery with Redis as the message broker will be used. When 50,000 students apply at the same time, instead of writing all of them directly to the database at once, each application request is placed into a queue. Celery workers then process these jobs one by one in the background at a controlled pace.

This way, the API responds to the user immediately without waiting for the database write to complete. The database does not get overwhelmed, and email notifications are sent asynchronously after the job is processed.

### 7. How will you scale the system?

The API layer will be scaled by running multiple Django instances behind an Nginx load balancer. The database will use a PostgreSQL primary instance for writes and one or more read replicas for heavy read operations. Redis will run as a cluster for distributed caching. Celery workers can be scaled horizontally by simply adding more worker processes when the queue grows. For file storage, AWS S3 or a similar service will be used. The entire system will be containerized using Docker and managed with Kubernetes for easy deployment and scaling.


# SECTION D 

### 1. Why is the query slow?

The query is slow for four main reasons.

There is no index on the internship_id column, so the database performs a full table scan going through all 10 million rows one by one instead of jumping directly to the matching records.

There is no index on the created_at column either, so after finding the matching rows, the database has to load them all into memory and sort them manually, which is very expensive.

The SELECT star fetches every column in the table including ones that are never used, which increases the amount of data read from disk unnecessarily.

Finally, there is no LIMIT clause, so all matching rows are returned at once which could be thousands of records.


### 2. How will you optimize it?

The first step is to select only the columns that are actually needed instead of using SELECT star. This reduces the amount of data fetched from disk.

The second step is to add a LIMIT clause with pagination so only 20 records are returned per request instead of all of them at once.

The third and most important step is to create a composite index on both the internship_id and created_at columns together. This single index can handle both the WHERE filter and the ORDER BY sorting at the same time, making the query dramatically faster.


### 3. What indexes will you create?

A composite index on internship_id and created_at together is the most important one. This handles the most common query pattern of filtering by internship and sorting by date in a single index scan.

A separate index on student_id is also created for queries that filter applications by student.


### 4. How will you measure performance improvement?

The EXPLAIN ANALYZE command in PostgreSQL will be run on the query both before and after adding the index. This shows exactly how the database is executing the query, what type of scan it is using, how many rows it is scanning, and how long it takes.

Before adding the index, the output will show a Sequential Scan going through all 10 million rows with a query time of around 2000ms. After adding the index, it will show an Index Scan going through only a few hundred rows with a query time of around 5 to 10ms.

# SECTION E 

### Backend Architecture for Internship Management Platform

The architecture is divided into five main layers.

The API layer is built with Django REST Framework. It handles all incoming HTTP requests and is responsible for authentication, internship management, application management, and analytics. JWT tokens are used for secure authentication.

The cache layer uses Redis to store frequently accessed data like internship listings. This prevents the database from being hit for every single request and keeps response times low.

The queue layer uses Celery with Redis as the broker. When a large number of applications come in at the same time, they are placed into a queue and processed by Celery workers in the background. This keeps the API fast and prevents the database from being overloaded.

The database layer uses PostgreSQL. A primary instance handles all write operations like creating and updating records. A read replica handles heavy read operations like listing and analytics queries. Proper indexes ensure queries remain fast even as the data grows.

The notification service handles sending emails and push notifications. It is triggered by Celery workers after events like a successful application or a status update. Emails are sent via SMTP using a service like SendGrid, and push notifications are sent via Firebase Cloud Messaging.

All five layers work together to ensure the system is fast, scalable, and reliable even under high traffic conditions.