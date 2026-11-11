# Comments SPA

A single-page application for threaded comments with file attachments,
CAPTCHA and real-time updates.

A full-stack project built to a commercial-style specification.

The whole stack runs locally with Docker — see
[Running in development](#running-in-development).

---

## Stack

**Backend:** Python 3.12, Django 5.2, Django REST Framework, Daphne (ASGI)
**Database:** MySQL 8.0
**Queue and cache:** Redis 7, Celery
**Real time:** Django Channels (WebSocket)
**Frontend:** Vue 3 (Composition API), Pinia, Vite, Axios
**Infrastructure:** Docker, Docker Compose, nginx, Let's Encrypt

---

## Features

### Comments

- Tree structure with unlimited nesting: any comment can be replied to,
  including a reply to a reply
- Root comments are shown in a table, sortable by User Name, E-mail and
  creation date — in both directions
- Default sort order is LIFO: newest first
- Pagination, 25 records per page
- A reply thread is loaded on demand, when the row is expanded

### Submission form

- Required fields: User Name, E-mail, CAPTCHA, message text
- Optional field: Home page, in URL format
- Validation on both the client and the server
- Message preview without a page reload
- A toolbar for inserting the allowed tags: `[i] [strong] [code] [a]`

### CAPTCHA

- The image is generated on the server with Pillow: a random code,
  interference lines, dot noise and a light blur
- The correct answer is kept in Redis and never sent to the client
- Single use: the key is deleted after the first check
- Lifetime of 10 minutes
- Clicking the image opens an enlarged version

### Attachments

- Images: JPG, PNG, GIF. Anything larger than 320×240 is scaled down
  proportionally with the LANCZOS filter
- Text files: TXT up to 100 KB
- The file type is detected from the content, not from the extension —
  a renamed executable will not pass
- Viewed in an animated modal: images open at full size, text files are
  shown with their formatting preserved

### Real time

- New comments appear for everyone with the page open, without a reload
- Automatic reconnection after a dropped connection, with a backoff
  growing from 1 to 30 seconds
- A periodic ping keeps proxies from closing an idle connection

---

## Security

**XSS.** Only four tags are allowed: `<a href="" title="">`, `<code>`,
`<i>`, `<strong>`. The text is sanitised with `bleach` against allow-lists
of tags, attributes and protocols — a link such as `javascript:alert(1)`
is neutralised. For `<a>`, only `href` and `title` are permitted.

**Markup validity.** The tag structure is checked with the `lxml` XML
parser: an unclosed tag and a broken nesting order are rejected with
distinct messages. XML entity substitution is disabled, which protects
against the billion laughs attack.

**SQL injection.** Every database query goes through the Django ORM,
which uses parameterised queries. No raw SQL is used in the project.

**Other.** Text length limits, file size limits, an allow-list of sortable
fields, a fixed page size, security HTTP headers and secure cookies in
production.

---

## Queue, cache, events and authentication

| Area | Implementation |
|---|---|
| **Queue** | Celery: cache invalidation after a comment is added, notification of the parent comment's author. Up to three retries on failure |
| **Cache** | Redis: Django cache and CAPTCHA storage |
| **Events** | Django `post_save` signals broadcast a new comment over WebSocket. The broadcast logic is kept separate from the creation logic |
| **JWT** | `djangorestframework-simplejwt`: 30-minute access token, 7-day refresh, rotation with a blacklist. Protects administrative actions |

Comments are anonymous by design, so the public endpoints are open.
JWT is required for deleting a comment.

---

## Running in development

Docker is all you need — Python, Node and MySQL do not have to be
installed on the machine.

```bash
git clone https://github.com/OleksandrHabelchenko/dzencode-comments.git
cd dzencode-comments
```

Create the settings file:

```bash
cp .env.example .env
```

Open `.env` and fill in three values:

```
SECRET_KEY=any_long_random_string
DB_PASSWORD=any_password
DB_ROOT_PASSWORD=another_password
```

Start the stack:

```bash
docker compose up -d --build
```

The first run takes a few minutes: images are built and the database is
initialised. Wait until the database is ready:

```bash
docker compose ps
```

The `db` service must show `healthy` in the STATUS column.

Apply the migrations and create an administrator:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

Done:

- Application — http://localhost:5173
- API — http://localhost:8000/api/comments/
- Admin — http://localhost:8000/admin

To stop: `docker compose down`

### Sample data

To check pagination and sorting:

```bash
docker compose exec backend python manage.py seed_comments --count 60
```

Creates 60 root comments with random replies.

---

## Running in production

```bash
git clone https://github.com/OleksandrHabelchenko/dzencode-comments.git
cd dzencode-comments
```

Create `.env` with production values:

```
DEBUG=False
SECRET_KEY=long_random_string
ALLOWED_HOSTS=your_domain,localhost,127.0.0.1,backend

DB_NAME=comments_db
DB_USER=comments_user
DB_PASSWORD=password
DB_ROOT_PASSWORD=root_password
DB_HOST=db
DB_PORT=3306

REDIS_HOST=redis
REDIS_PORT=6379

CORS_ALLOWED_ORIGINS=https://your_domain
CSRF_TRUSTED_ORIGINS=https://your_domain
SECURE_COOKIES=True
NGINX_CONF=nginx-ssl.conf
```

Set `SECURE_COOKIES` to `False` if the site runs over plain HTTP:
otherwise the browser will not send the cookies and form submissions will
fail the check. `NGINX_CONF` selects the nginx configuration — without
HTTPS, use `nginx.conf`.

Start:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Migrations and static file collection run automatically on container
start.

### HTTPS

```bash
mkdir -p certbot/conf certbot/www
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d your_domain --email your@email --agree-tos --no-eff-email
```

Once the certificate is issued, set `NGINX_CONF=nginx-ssl.conf` in `.env`
and restart nginx. Automatic renewal is set up with a cron job.

**How production differs from development:**

- Daphne instead of `runserver`
- Vue is built into static files, Vite does not run
- nginx serves the static files and proxies the API, the admin panel and
  the WebSocket
- Only ports 80 and 443 are exposed; the database and Redis are reachable
  only inside the Docker network
- The code lives inside the image instead of being mounted from disk

---

## Project structure

```
dzencode-comments/
├── backend/
│   ├── comments/
│   │   ├── models.py              Comment and Attachment models
│   │   ├── serializers.py         DRF serializers
│   │   ├── views.py               API endpoints
│   │   ├── captcha.py             CAPTCHA generation and verification
│   │   ├── text_validation.py     tag and XHTML checks, XSS protection
│   │   ├── file_validation.py     attachment handling, image resizing
│   │   ├── tasks.py               Celery background tasks
│   │   ├── consumers.py           WebSocket handler
│   │   ├── signals.py             event broadcasting
│   │   ├── routing.py             WebSocket routes
│   │   └── management/commands/
│   │       └── seed_comments.py   sample data generator
│   └── config/
│       ├── settings.py
│       ├── urls.py                HTTP routes
│       ├── asgi.py                ASGI entry point
│       └── celery.py              Celery configuration
├── frontend/
│   ├── Dockerfile                 development image
│   ├── Dockerfile.prod            multi-stage production build
│   └── src/
│       ├── api/                   API layer
│       ├── components/            UI components
│       ├── composables/           validation, WebSocket
│       ├── stores/                Pinia store
│       └── styles/                global styles
├── docker/
│   ├── nginx.conf                 nginx configuration without HTTPS
│   └── nginx-ssl.conf             nginx configuration with HTTPS
├── docs/
│   └── schema.sql                 database schema for MySQL Workbench
├── docker-compose.yml             development environment
└── docker-compose.prod.yml        production environment
```

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/comments/` | Table of root comments. Parameters: `page`, `ordering`, `direction` |
| POST | `/api/comments/` | Create a comment or a reply (multipart/form-data) |
| GET | `/api/comments/<id>/` | A comment with its full reply tree |
| DELETE | `/api/comments/<id>/delete/` | Delete. Requires an administrator JWT |
| GET | `/api/comments/captcha/` | A new CAPTCHA: key and image |
| POST | `/api/auth/token/` | Obtain a token pair from username and password |
| POST | `/api/auth/token/refresh/` | Refresh the access token |
| POST | `/api/auth/token/verify/` | Verify a token |
| WS | `/ws/comments/` | Subscribe to new comments |

**Sorting:** `?ordering=user_name&direction=asc`
Allowed fields: `user_name`, `email`, `created_at`.
Direction: `asc`, `desc`. Defaults to `created_at` + `desc`.

---

## Database schema

The file `docs/schema.sql` was produced with `mysqldump` from the running
database and opens in MySQL Workbench:
**File → Import → Reverse Engineer MySQL Create Script**

### Comment

| Field | Type | Description |
|---|---|---|
| id | BIGINT | Primary key |
| parent_id | BIGINT NULL | Reference to the parent comment. NULL means a root comment |
| root_id | BIGINT NULL | Reference to the root of the thread. Denormalised for speed |
| user_name | VARCHAR(50) | User name |
| email | VARCHAR(254) | E-mail |
| home_page | VARCHAR(200) | Home page, optional |
| text | LONGTEXT | Message text |
| created_at | DATETIME | Creation date, indexed |
| ip_address | CHAR(39) | Client IP, filled in by the server |
| user_agent | LONGTEXT | Browser User-Agent |

The `root_id` field makes it possible to fetch every descendant of a
thread in a single query instead of walking the levels recursively.

### Attachment

| Field | Type | Description |
|---|---|---|
| id | BIGINT | Primary key |
| comment_id | BIGINT UNIQUE | One-to-one link to a comment |
| file | VARCHAR(100) | File path |
| file_type | VARCHAR(10) | `image` or `text` |
| original_name | VARCHAR(255) | Original file name |
| width, height | INT NULL | Image dimensions after processing |
| uploaded_at | DATETIME | Upload date |

---

## Git branching

- `main` — the stable version
- `develop` — the main development branch
- `feature/*` — a separate branch for each task

Every feature was developed in its own branch and merged into `develop`
after review. Commit messages follow Conventional Commits.
