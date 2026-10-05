"""
Janseva AI — Database Client
Provides Supabase client instances for authenticated and service-role access,
with direct PostgreSQL fallback when Supabase REST API keys are not provisioned.
"""
from typing import Optional, Any, List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
import json
import uuid
import structlog
from app.config import get_settings

logger = structlog.get_logger()

# Connection pool for direct Postgres access
_db_pool: Optional[ThreadedConnectionPool] = None

def get_connection_pool() -> Optional[ThreadedConnectionPool]:
    global _db_pool
    if _db_pool is None:
        settings = get_settings()
        db_url = settings.database_url or "postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
        try:
            _db_pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=db_url)
            logger.info("postgres_connection_pool_initialized")
        except Exception as e:
            logger.error("postgres_connection_pool_error", error=str(e))
            return None
    return _db_pool

@contextmanager
def get_db_connection():
    pool = get_connection_pool()
    if not pool:
        settings = get_settings()
        db_url = settings.database_url or "postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
        conn = psycopg2.connect(db_url)
        try:
            yield conn
        finally:
            conn.close()
        return

    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


def _sanitize_value(v):
    if hasattr(v, "value"):
        v = v.value
    if isinstance(v, dict):
        return Json(v)
    if isinstance(v, list):
        if v and isinstance(v[0], dict):
            return Json(v)
        return v
    return v


class APIResponse:
    def __init__(self, data: Any, count: Optional[int] = None):
        self.data = data
        self.count = count if count is not None else (len(data) if isinstance(data, list) else 0)


class PostgresQueryBuilder:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.op = "SELECT"
        self.columns = "*"
        self.where_clauses: List[str] = []
        self.where_params: List[Any] = []
        self.order_by: Optional[str] = None
        self.limit_val: Optional[int] = None
        self.offset_val: Optional[int] = None
        self.count_mode: Optional[str] = None
        self.is_single: bool = False
        self.insert_data: Optional[List[Dict[str, Any]]] = None
        self.update_data: Optional[Dict[str, Any]] = None

    def select(self, columns: str = "*", count: Optional[str] = None):
        self.op = "SELECT"
        self.columns = columns
        self.count_mode = count
        return self

    def insert(self, data: Any):
        self.op = "INSERT"
        self.insert_data = data if isinstance(data, list) else [data]
        return self

    def update(self, data: Dict[str, Any]):
        self.op = "UPDATE"
        self.update_data = data
        return self

    def delete(self):
        self.op = "DELETE"
        return self

    def eq(self, column: str, value: Any):
        self.where_clauses.append(f'"{column}" = %s')
        self.where_params.append(_sanitize_value(value))
        return self

    def neq(self, column: str, value: Any):
        self.where_clauses.append(f'"{column}" != %s')
        self.where_params.append(_sanitize_value(value))
        return self

    def in_(self, column: str, values: List[Any]):
        if not values:
            self.where_clauses.append("1=0")
        else:
            placeholders = ", ".join(["%s"] * len(values))
            self.where_clauses.append(f'"{column}" IN ({placeholders})')
            self.where_params.extend([_sanitize_value(val) for val in values])
        return self

    def is_(self, column: str, value: Any):
        if str(value).lower() in ("null", "none"):
            self.where_clauses.append(f'"{column}" IS NULL')
        else:
            self.where_clauses.append(f'"{column}" IS %s')
            self.where_params.append(_sanitize_value(value))
        return self

    def gte(self, column: str, value: Any):
        self.where_clauses.append(f'"{column}" >= %s')
        self.where_params.append(_sanitize_value(value))
        return self

    def lte(self, column: str, value: Any):
        self.where_clauses.append(f'"{column}" <= %s')
        self.where_params.append(_sanitize_value(value))
        return self

    def gt(self, column: str, value: Any):
        self.where_clauses.append(f'"{column}" > %s')
        self.where_params.append(_sanitize_value(value))
        return self

    def lt(self, column: str, value: Any):
        self.where_clauses.append(f'"{column}" < %s')
        self.where_params.append(_sanitize_value(value))
        return self

    def order(self, column: str, desc: bool = False):
        direction = "DESC" if desc else "ASC"
        self.order_by = f'"{column}" {direction}'
        return self

    def range(self, start: int, end: int):
        self.offset_val = start
        self.limit_val = (end - start + 1)
        return self

    def limit(self, count: int):
        self.limit_val = count
        return self

    def single(self):
        self.is_single = True
        self.limit_val = 1
        return self

    def execute(self) -> APIResponse:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            try:
                if self.op == "INSERT":
                    results = []
                    for row in (self.insert_data or []):
                        cols = []
                        vals = []
                        for k, v in row.items():
                            cols.append(f'"{k}"')
                            vals.append(_sanitize_value(v))
                        placeholders = ", ".join(["%s"] * len(vals))
                        sql = f'INSERT INTO "{self.table_name}" ({", ".join(cols)}) VALUES ({placeholders}) RETURNING *'
                        cur.execute(sql, vals)
                        inserted = dict(cur.fetchone())
                        results.append(inserted)
                    conn.commit()
                    return APIResponse(results)

                elif self.op == "UPDATE":
                    set_clauses = []
                    set_params = []
                    for k, v in (self.update_data or {}).items():
                        if v == "now()":
                            set_clauses.append(f'"{k}" = NOW()')
                        else:
                            set_clauses.append(f'"{k}" = %s')
                            set_params.append(_sanitize_value(v))
                    sql = f'UPDATE "{self.table_name}" SET {", ".join(set_clauses)}'
                    params = list(set_params)
                    if self.where_clauses:
                        sql += " WHERE " + " AND ".join(self.where_clauses)
                        params.extend(self.where_params)
                    sql += " RETURNING *"
                    cur.execute(sql, params)
                    rows = [dict(r) for r in cur.fetchall()]
                    conn.commit()
                    return APIResponse(rows)

                elif self.op == "DELETE":
                    sql = f'DELETE FROM "{self.table_name}"'
                    if self.where_clauses:
                        sql += " WHERE " + " AND ".join(self.where_clauses)
                    sql += " RETURNING *"
                    cur.execute(sql, self.where_params)
                    rows = [dict(r) for r in cur.fetchall()]
                    conn.commit()
                    return APIResponse(rows)

                elif self.op == "SELECT":
                    total_count = None
                    if self.count_mode:
                        count_sql = f'SELECT COUNT(*) FROM "{self.table_name}"'
                        if self.where_clauses:
                            count_sql += " WHERE " + " AND ".join(self.where_clauses)
                        cur.execute(count_sql, self.where_params)
                        count_res = cur.fetchone()
                        total_count = count_res["count"] if count_res else 0

                    clean_cols = "*" if "(" in self.columns else self.columns
                    sql = f'SELECT {clean_cols} FROM "{self.table_name}"'
                    if self.where_clauses:
                        sql += " WHERE " + " AND ".join(self.where_clauses)
                    if self.order_by:
                        sql += f" ORDER BY {self.order_by}"
                    if self.limit_val is not None:
                        sql += f" LIMIT {self.limit_val}"
                    if self.offset_val is not None:
                        sql += f" OFFSET {self.offset_val}"

                    cur.execute(sql, self.where_params)
                    rows = [dict(r) for r in cur.fetchall()]

                    # Resolve joins if requested in columns query
                    if "(" in self.columns:
                        for r in rows:
                            if "department_id" in r and r.get("department_id") and "departments" in self.columns:
                                cur.execute('SELECT name FROM departments WHERE id = %s', (r["department_id"],))
                                d = cur.fetchone()
                                r["departments"] = dict(d) if d else None
                            if "location_id" in r and r.get("location_id") and "locations" in self.columns:
                                cur.execute('SELECT * FROM locations WHERE id = %s', (r["location_id"],))
                                l = cur.fetchone()
                                r["locations"] = dict(l) if l else None
                            if "user_id" in r and r.get("user_id") and "user_profiles" in self.columns:
                                cur.execute('SELECT full_name, role, phone FROM user_profiles WHERE id = %s', (r["user_id"],))
                                u = cur.fetchone()
                                r["user_profiles"] = dict(u) if u else None
                            if "team_id" in r and r.get("team_id") and "teams" in self.columns:
                                cur.execute('SELECT name FROM teams WHERE id = %s', (r["team_id"],))
                                t = cur.fetchone()
                                r["teams"] = dict(t) if t else None
                            if "worker_skills" in self.columns and "id" in r:
                                try:
                                    cur.execute('SELECT s.name FROM worker_skills ws JOIN skills s ON ws.skill_id = s.id WHERE ws.worker_id = %s', (r["id"],))
                                    skills = cur.fetchall()
                                    r["worker_skills"] = [{"skills": {"name": sk["name"]}} for sk in skills] if skills else []
                                except Exception:
                                    r["worker_skills"] = []
                            if "complaints" in self.columns and "complaint_id" in r and r.get("complaint_id"):
                                cur.execute('SELECT * FROM complaints WHERE id = %s', (r["complaint_id"],))
                                c = cur.fetchone()
                                r["complaints"] = dict(c) if c else None
                            if "task_id" in r and r.get("task_id") and "tasks" in self.columns:
                                cur.execute('SELECT * FROM tasks WHERE id = %s', (r["task_id"],))
                                task_row = cur.fetchone()
                                if task_row:
                                    t_dict = dict(task_row)
                                    if t_dict.get("location_id"):
                                        cur.execute('SELECT * FROM locations WHERE id = %s', (t_dict["location_id"],))
                                        loc_row = cur.fetchone()
                                        t_dict["locations"] = dict(loc_row) if loc_row else None
                                    r["tasks"] = t_dict
                                else:
                                    r["tasks"] = None

                    if self.is_single:
                        return APIResponse(rows[0] if rows else None, total_count)
                    return APIResponse(rows, total_count)

            finally:
                cur.close()


class PostgresSupabaseClient:
    def table(self, table_name: str) -> PostgresQueryBuilder:
        return PostgresQueryBuilder(table_name)


_admin_client: Optional[Any] = None

def get_supabase_admin() -> Any:
    """Returns the database client (Postgres direct adapter or Supabase REST Client)."""
    global _admin_client
    if _admin_client is None:
        settings = get_settings()
        # If real service role key is provided, use official Supabase client
        if (
            settings.supabase_service_role_key
            and not "placeholder" in settings.supabase_service_role_key
            and settings.supabase_service_role_key.startswith("ey")
        ):
            try:
                from supabase import create_client
                _admin_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
                return _admin_client
            except Exception as e:
                logger.warning("supabase_client_fallback_to_postgres", error=str(e))
        
        # Fallback to direct Postgres driver for 100% reliable execution
        _admin_client = PostgresSupabaseClient()
    return _admin_client


def get_supabase_client() -> Any:
    return get_supabase_admin()


def get_authenticated_client(access_token: str) -> Any:
    return get_supabase_admin()
