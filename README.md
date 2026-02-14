# Nucleus

**Nucleus** is the central database management service of the system.
Inspired by the biological cell nucleus, it acts as the single source of truth,
governing how data is stored, structured, and maintained across all backends.

Nucleus provides a stable and consistent foundation for data persistence,
schema evolution, and integrity, enabling other services to focus on
processing, signaling, and orchestration.

---

## Concept

**Biological Analogy:** Cell Nucleus  
In biology, the nucleus stores genetic information and regulates cellular activity.
Likewise, Nucleus stores core data and enforces rules that keep the system coherent
and reliable.

---

## Responsibilities

- Centralized data storage and persistence
- Schema definition and migration management
- Data integrity and consistency enforcement
- Transaction and concurrency control
- Backup, restore, and recovery coordination
- Providing a single source of truth for the system

---

## Non-Goals

- Business logic processing (handled by Metaflow)
- Event propagation or signaling (handled by Synapse)
- Authentication or authorization logic (handled by LymphHub)
- Data ingestion or classification (handled by Taxon)

---

## Architecture Position

[ Taxon ] → [ Metaflow ] → [ Nucleus ]
↓
[ Synapse ]
↓
[ LymphHub ]


Nucleus sits at the core of the architecture, supporting all services that
require reliable and consistent data access.

---

## Design Principles

- **Consistency over convenience**
- **Explicit schema evolution**
- **Strong ownership of data boundaries**
- **Predictable and observable behavior**
- **Failure-aware and recovery-first design**

---

## Example Use Cases

- Persisting classified data from Taxon
- Storing workflow state and checkpoints from Metaflow
- Maintaining event durability for Synapse
- Providing secure, authoritative data access for authenticated services

---

## Naming Rationale

The name *Nucleus* reflects its role as the system’s data core:
a protected, authoritative center that maintains order and continuity
as the system grows and evolves.

---

## Status

🚧 Under active development  
Interfaces and responsibilities may evolve as the system architecture matures.

## how to 

```bash
python3 -m venv venv

# virtual  (Linux/Mac)
source venv/bin/activate

# virtual (Windows)
venv\Scripts\activate

# library install
python3 -m pip install -r requirements.txt

# 8011 port fastAPI execution
uvicorn main:app --port 8011
```

## test
```bash
POST /api/database/create
{
  "new_db": "my_database",
  "new_pass": "secure_password123",
  "new_user": "my_user"
}
POST /api/table/create
{
  "create_sql": "CREATE TABLE ci_projects (\n    id SERIAL PRIMARY KEY,\n    service_name VARCHAR(50) UNIQUE,\n    repo_url TEXT NOT NULL,\n    branch VARCHAR(50) DEFAULT 'main',\n    registry_url TEXT\n);",
  "grant_user": "my_user",
  "target_db": "my_database"
}
```

## docker image managing
# ${DOMAIN}
```bash
docker login registry.${DOMAIN} -u ${REGISTRY_USER} --password-stdin

docker build \
    --build-arg BUILD_ENV=${DEPLOY_ENV} \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg BUILD_VERSION=${IMAGE_TAG} \
    --build-arg VCS_REF=$(git rev-parse --short HEAD) \
    -t registry.${DOMAIN}/${IMAGE_NAME}:${IMAGE_TAG} \
    -t registry.${DOMAIN}/${IMAGE_NAME}:latest .

# tag push
docker push registry.${DOMAIN}/${IMAGE_NAME}:${IMAGE_TAG}
docker push registry.${DOMAIN}/${IMAGE_NAME}:latest

docker logout registry.${DOMAIN}
```