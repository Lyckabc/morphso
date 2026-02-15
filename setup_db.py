import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()


class DbAccountConfig:
    """관리자 DB 계정 정보를 저장하고 로드하는 클래스."""

    def __init__(self, admin_user=None, admin_password=None, host=None, port=None):
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.host = host
        self.port = port
        self.dbname = None

    def load_from_env(self):
        """환경 변수에서 계정 정보를 로드하여 인스턴스에 저장한다."""
        self.admin_user = os.getenv("DB_ADMIN_USER", "postgres")
        self.admin_password = os.getenv("DB_ADMIN_PASSWORD")
        self.host = os.getenv("DB_ADMIN_HOST", "localhost")
        self.port = os.getenv("DB_ADMIN_PORT", "5432")
        self.dbname = os.getenv("DB_ADMIN_DBNAME", "postgres")
        return self

    def health_check(self, dbname="postgres"):
        """
        저장된 계정 정보로 DB 연결을 시도하고 상태를 반환한다.
        Returns: dict with status, db, admin_user, host (and error if failed)
        """
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=self.admin_user,
                password=self.admin_password,
                host=self.host,
                port=self.port,
                connect_timeout=5,
            )
            conn.close()
            return {
                "status": "healthy",
                "db": dbname,
                "admin_user": self.admin_user,
                "host": self.host,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "db": dbname,
                "admin_user": self.admin_user,
                "host": self.host,
                "error": str(e),
            }


def create_database_and_user(new_db=None, new_user=None, new_pass=None, account=None):
    """
    새 DB와 사용자를 생성한다.
    account가 없으면 DbAccountConfig().load_from_env()로 로드한 계정을 사용한다.
    """
    if account is None:
        account = DbAccountConfig().load_from_env()
    admin_user = account.admin_user
    admin_password = account.admin_password
    host = account.host
    port = account.port

    # 파라미터가 제공되지 않으면 환경 변수에서 가져오기
    new_db = new_db or os.getenv("NEW_DB_NAME")
    new_user = new_user or os.getenv("NEW_DB_USER")
    new_pass = new_pass or os.path.expandvars(os.getenv("NEW_DB_PASSWORD") or "")

    # 필수 파라미터 검증
    if not new_db or not new_user or not new_pass:
        raise ValueError("new_db, new_user, and new_pass are required")

    try:
        # 1. 관리자(postgres) DB에 연결
        conn = psycopg2.connect(
            dbname="postgres",
            user=admin_user,
            password=admin_password,
            host=host,
            port=port,
        )
        conn.autocommit = True  # DB 생성 시 트랜잭션 방지 설정
        cur = conn.cursor()

        # 2. 사용자(User) 생성 및 Superuser 권한 부여
        print(f"Checking if user '{new_user}' exists...")
        cur.execute(sql.SQL("SELECT 1 FROM pg_roles WHERE rolname = %s"), [new_user])
        if not cur.fetchone():
            cur.execute(
                sql.SQL("CREATE USER {} WITH SUPERUSER PASSWORD %s").format(
                    sql.Identifier(new_user)
                ),
                [new_pass],
            )
            print(f"User '{new_user}' created with Superuser privileges.")
        else:
            print(f"User '{new_user}' already exists.")

        # 3. 데이터베이스(Database) 생성
        print(f"Checking if database '{new_db}' exists...")
        cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [new_db])
        if not cur.fetchone():
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(new_db), sql.Identifier(new_user)
                )
            )
            print(f"Database '{new_db}' created successfully.")
        else:
            print(f"Database '{new_db}' already exists.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        raise


def create_table(target_db, create_sql, grant_user, account=None):
    """
    target_db에 create_sql을 실행하여 테이블을 만들고, grant_user에게 해당 DB 및 테이블 권한을 부여한다.
    create_sql은 예: '''CREATE TABLE ci_projects (...);''' 형태의 raw SQL 문자열.
    """
    if account is None:
        account = DbAccountConfig().load_from_env()
    admin_user = account.admin_user
    admin_password = account.admin_password
    host = account.host
    port = account.port

    if not target_db or not create_sql or not grant_user:
        raise ValueError("target_db, create_sql, and grant_user are required")

    create_sql = create_sql.strip()
    if not create_sql.rstrip(";").strip().upper().startswith("CREATE"):
        raise ValueError("create_sql must be a CREATE TABLE (or CREATE) statement")

    try:
        conn = psycopg2.connect(
            dbname=target_db,
            user=admin_user,
            password=admin_password,
            host=host,
            port=port,
        )
        conn.autocommit = True
        cur = conn.cursor()

        # 1. CREATE TABLE 실행
        cur.execute(create_sql)
        print(f"Table(s) created in database '{target_db}'.")

        # 2. grant_user에게 DB 및 public 스키마 테이블 권한 부여
        cur.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(target_db), sql.Identifier(grant_user)
            )
        )
        grant_user_id = sql.Identifier(grant_user)
        cur.execute(
            sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(grant_user_id)
        )
        cur.execute(
            sql.SQL(
                "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}"
            ).format(grant_user_id)
        )
        cur.execute(
            sql.SQL(
                "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}"
            ).format(grant_user_id)
        )
        cur.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}"
            ).format(grant_user_id)
        )
        cur.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}"
            ).format(grant_user_id)
        )
        print(f"Granted database and table privileges to user '{grant_user}'.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    create_database_and_user()