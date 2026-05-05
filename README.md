# Ecommerce Task API

A RESTful ecommerce backend built with **FastAPI**, **MySQL**, and **Redis**.

---

## Project Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose

### Local Setup (without Docker)

```bash
# 1. Clone the repo
git clone <repo-url>
cd task-api

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env file
cp .env.example .env

# 5. Run migrations
alembic upgrade head

# 6. Start the server
uvicorn main:app --reload
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
APP_NAME=Ecommerce API
ENV=development

# Database
DB_HOST=mysql
DB_PORT=3306
DB_NAME=ecommerce_db
DB_USER=root
DB_PASSWORD=<your_db_password>

# JWT
JWT_SECRET=<your_jwt_secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MIN=60

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

> For local setup (without Docker), set `DB_HOST=localhost` and `REDIS_HOST=localhost`.

---

## Docker Run Steps

```bash
# 1. Build and start all services
docker-compose up --build

# 2. Run in detached mode
docker-compose up -d --build

# 3. Run DB migrations inside the container
docker exec -it ecommerce-api alembic upgrade head

# 4. Stop all services
docker-compose down
```

Services started:
| Service | Port |
|---------|------|
| API | http://localhost:8000 |
| MySQL | localhost:3307 |
| Redis | localhost:6379 |

---

## API Docs

Once the server is running, visit:

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc (readable) |
| http://localhost:8000/health | Health check (DB + Redis status) |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Register user |
| POST | `/login` | No | Login, get JWT token |
| GET | `/products` | No | List products (filter, search, sort, paginate) |
| POST | `/products` | No | Create product |
| GET | `/products/{id}` | No | Get single product |
| PUT | `/products/{id}` | No | Update product |
| DELETE | `/products/{id}` | No | Delete product |
| GET | `/cart` | Yes | Get user cart |
| POST | `/cart` | Yes | Add item to cart |
| DELETE | `/cart/{id}` | Yes | Remove cart item |
| POST | `/orders` | Yes | Create order from cart |
| POST | `/orders/place` | Yes | Place order (optimized) |
| GET | `/orders` | Yes | Get user orders |
| GET | `/addresses` | Yes | List addresses |
| POST | `/addresses` | Yes | Add address |
| PUT | `/addresses/{id}` | Yes | Update address |
| DELETE | `/addresses/{id}` | Yes | Delete address |

> Authenticated routes require `Authorization: Bearer <token>` header.

---

## Folder Structure

```
task-api/
├── alembic/                  # DB migrations
│   └── versions/
├── config/
│   ├── config.py             # App settings (env vars)
│   └── redis_config.py       # Redis client setup
├── models/                   # SQLAlchemy ORM models
│   ├── user.py
│   ├── product.py
│   ├── cart.py
│   └── order.py
├── routers/                  # Route handlers
│   ├── auth.py
│   ├── product.py
│   ├── cart.py
│   ├── order.py
│   ├── address.py
│   └── health.py
├── schemas/                  # Pydantic request/response schemas
│   ├── user.py
│   ├── product.py
│   ├── cart.py
│   ├── order.py
│   └── address.py
├── utils/
│   ├── auth.py               # JWT + password hashing
│   ├── email.py              # Background email sender
│   └── logger.py             # Request logger
├── .env                      # Environment variables
├── alembic.ini               # Alembic config
├── database.py               # DB engine + session
├── docker-compose.yml        # Docker services
├── Dockerfile                # API container
├── main.py                   # App entry point
└── requirements.txt          # Python dependencies
```
