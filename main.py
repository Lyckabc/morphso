from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import setup_db
from infisical_router import router as infisical_router

app = FastAPI(
    title="Morphso Database Management API",
    description="Central database management service for creating databases and users",
    version="1.0.0"
)
app.include_router(infisical_router)


class DatabaseCreateRequest(BaseModel):
    new_db: str = Field(..., description="Name of the new database to create", min_length=1)
    new_user: str = Field(..., description="Name of the new database user to create", min_length=1)
    new_pass: str = Field(..., description="Password for the new database user", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "new_db": "my_database",
                "new_user": "my_user",
                "new_pass": "secure_password123"
            }
        }


class DatabaseCreateResponse(BaseModel):
    success: bool
    message: str
    database: Optional[str] = None
    user: Optional[str] = None


class TableCreateRequest(BaseModel):
    target_db: str = Field(..., description="Database where the table will be created", min_length=1)
    create_sql: str = Field(
        ...,
        description="Raw CREATE TABLE SQL (e.g. CREATE TABLE ci_projects (...);)",
        min_length=1,
    )
    grant_user: str = Field(
        ...,
        description="User to grant database and table privileges to",
        min_length=1,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "target_db": "my_database",
                "create_sql": """CREATE TABLE ci_projects (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) UNIQUE,
    repo_url TEXT NOT NULL,
    branch VARCHAR(50) DEFAULT 'main',
    registry_url TEXT
);""",
                "grant_user": "my_user",
            }
        }


class TableCreateResponse(BaseModel):
    success: bool
    message: str
    database: Optional[str] = None
    grant_user: Optional[str] = None


@app.get("/")
async def root():
    return {
        "message": "Morphso Database Management API",
        "version": "1.0.0",
        "endpoints": {
            "create_database": "/api/v1/rdb/database/create",
            "create_table": "/api/v1/rdb/table/create",
            "health": "/health",
            "secret": "/api/v1/secret"
        }
    }


@app.get("/health")
async def health_check():
    """Checks the DB connection status using stored account information and returns connection details."""
    account = setup_db.DbAccountConfig().load_from_env()
    result = account.health_check(dbname="postgres")
    return result


@app.post("/api/v1/rdb/database/create", response_model=DatabaseCreateResponse)
async def create_database(request: DatabaseCreateRequest):
    """
    Create a new PostgreSQL database and user.
    
    This endpoint creates:
    - A new PostgreSQL user with SUPERUSER privileges
    - A new PostgreSQL database owned by the new user
    
    If the user or database already exists, they will be skipped.
    """
    try:
        account = setup_db.DbAccountConfig().load_from_env()
        setup_db.create_database_and_user(
            new_db=request.new_db,
            new_user=request.new_user,
            new_pass=request.new_pass,
            account=account,
        )
        
        return DatabaseCreateResponse(
            success=True,
            message=f"Database '{request.new_db}' and user '{request.new_user}' created successfully",
            database=request.new_db,
            user=request.new_user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create database: {str(e)}"
        )


@app.post("/api/v1/rdb/table/create", response_model=TableCreateResponse)
async def create_table(request: TableCreateRequest):
    """
    Create a table in the target database using the provided SQL,
    then grant the specified user privileges on the database and tables.
    """
    try:
        account = setup_db.DbAccountConfig().load_from_env()
        setup_db.create_table(
            target_db=request.target_db,
            create_sql=request.create_sql,
            grant_user=request.grant_user,
            account=account,
        )
        return TableCreateResponse(
            success=True,
            message=f"Table created in '{request.target_db}' and privileges granted to '{request.grant_user}'",
            database=request.target_db,
            grant_user=request.grant_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to create table. Please check the server logs for details.",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
