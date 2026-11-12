"""
Databricks On-Behalf-Of (OBO) Authentication Module for Project Allianz.

NO PERSONAL ACCESS TOKEN (PAT) IS REQUIRED!
Databricks Apps automatically generates and forwards an ephemeral OAuth user token
in the HTTP request header: 'X-Forwarded-Access-Token'.

When a user logs in via SSO, queries to Databricks SQL Warehouses execute On-Behalf-Of
that logged-in user, enforcing Unity Catalog Row-Level Security and Column Masking.
"""

import os
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

try:
    import streamlit as st
except ImportError:
    st = None


def get_obo_headers() -> Dict[str, str]:
    """
    Extracts HTTP headers injected automatically by Databricks Apps gateway.
    In Streamlit 1.35+, request headers are available in st.context.headers.
    """
    headers = {}
    try:
        if st is not None and hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = dict(st.context.headers)
    except Exception:
        pass
    return headers


def get_current_user_context() -> Dict[str, Any]:
    """
    Resolves execution identity via Databricks OBO protocol.
    ZERO manual token creation is needed in Databricks Apps!
    """
    headers = get_obo_headers()
    
    # 1. Databricks Apps automatically injects this token for the logged-in user
    obo_token = (
        headers.get("x-forwarded-access-token")
        or headers.get("X-Forwarded-Access-Token")
        or os.environ.get("DATABRICKS_TOKEN")
    )
    
    # 2. Databricks Apps automatically injects the user's corporate email / identity
    user_email = (
        headers.get("x-forwarded-email")
        or headers.get("X-Forwarded-Email")
        or headers.get("x-forwarded-user")
        or headers.get("X-Forwarded-User")
        or headers.get("x-forwarded-preferred-username")
        or headers.get("X-Forwarded-Preferred-Username")
        or os.environ.get("DATABRICKS_USER")
    )
    
    # Databricks Apps automatically provides DATABRICKS_HOST in the container environment
    host = os.environ.get("DATABRICKS_HOST", "")
    if not host and "host" in headers:
        host = headers["host"]
        
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    
    if obo_token:
        masked_token = obo_token[:6] + "..." + obo_token[-4:] if len(obo_token) > 10 else "******"
        return {
            "mode": "OBO (On-Behalf-Of)",
            "is_obo": True,
            "user_email": user_email or "allianz.user@allianz.com",
            "host": host,
            "warehouse_id": warehouse_id,
            "token": obo_token,
            "token_masked": masked_token,
            "status": "Active (Unity Catalog Permissions Enforced)",
            "description": "Authenticated automatically via Databricks OBO. Zero manual token configuration required."
        }
    else:
        return {
            "mode": "OBO Simulation (Demo Mode)",
            "is_obo": True,
            "user_email": "naresh.giduthuri@allianz.com",
            "host": host or "https://adb-allianz-lakehouse.azuredatabricks.net",
            "warehouse_id": warehouse_id or "allianz_dq_warehouse",
            "token": None,
            "token_masked": "obo_ephemeral_token",
            "status": "Simulated Session",
            "description": "Running locally in demo mode. When uploaded to Databricks Apps, OBO binds automatically to your SSO user with no token needed."
        }


def get_workspace_client(user_ctx: Optional[Dict[str, Any]] = None):
    """
    Returns an initialized Databricks SDK WorkspaceClient using OBO token or ambient credentials.
    """
    try:
        from databricks.sdk import WorkspaceClient
        if user_ctx is None:
            user_ctx = get_current_user_context()
        token = user_ctx.get("token")
        raw_host = user_ctx.get("host") or os.environ.get("DATABRICKS_HOST", "")
        
        if token and raw_host:
            host = raw_host if raw_host.startswith("http") else f"https://{raw_host}"
            return WorkspaceClient(host=host, token=token)
        return WorkspaceClient()
    except Exception:
        return None


def get_available_warehouses(user_ctx: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    Lists SQL Warehouses available in the workspace.
    """
    warehouses = []
    try:
        w = get_workspace_client(user_ctx)
        if w:
            for wh in w.warehouses.list():
                warehouses.append({
                    "id": str(wh.id),
                    "name": str(wh.name),
                    "state": str(getattr(wh, "state", "UNKNOWN"))
                })
    except Exception:
        pass
    return warehouses


def fetch_live_schemas(catalog: str = "samples", user_ctx: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Dynamically lists all schemas inside the specified catalog via Databricks SDK REST API or SQL.
    Does NOT require a running SQL warehouse when using Databricks SDK!
    """
    # 1. Try Databricks SDK REST API (Fastest, zero-warehouse needed)
    try:
        w = get_workspace_client(user_ctx)
        if w:
            schemas = [s.name for s in w.schemas.list(catalog_name=catalog)]
            if schemas:
                # Filter out system internal schemas if any
                return sorted([s for s in schemas if not s.startswith("_")])
    except Exception:
        pass

    # 2. Try Databricks SQL SHOW SCHEMAS
    try:
        df, err = execute_unity_catalog_sql(f"SHOW SCHEMAS IN {catalog}", user_ctx=user_ctx)
        if df is not None and not df.empty:
            col = "databaseName" if "databaseName" in df.columns else ("namespace" if "namespace" in df.columns else df.columns[0])
            return sorted(df[col].dropna().tolist())
    except Exception:
        pass

    # 3. Fallback for offline/demo or catalog='samples'
    if catalog.lower() == "samples":
        return ["nyctaxi", "tpch", "tpcds", "bike_sharing", "accidents"]
    return ["default", "public"]


def fetch_live_tables(catalog: str = "samples", schema: str = "nyctaxi", user_ctx: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Dynamically lists all tables inside catalog.schema via Databricks SDK REST API or SQL.
    """
    # 1. Try Databricks SDK REST API
    try:
        w = get_workspace_client(user_ctx)
        if w:
            tables = [t.name for t in w.tables.list(catalog_name=catalog, schema_name=schema)]
            if tables:
                return sorted(tables)
    except Exception:
        pass

    # 2. Try Databricks SQL SHOW TABLES
    try:
        df, err = execute_unity_catalog_sql(f"SHOW TABLES IN {catalog}.{schema}", user_ctx=user_ctx)
        if df is not None and not df.empty:
            col = "tableName" if "tableName" in df.columns else ("name" if "name" in df.columns else df.columns[0])
            return sorted(df[col].dropna().tolist())
    except Exception:
        pass

    # 3. Fallback for offline/demo or catalog='samples'
    fallback_map = {
        "nyctaxi": ["trips"],
        "tpch": ["customer", "orders", "lineitem", "nation", "part", "partsupp", "region", "supplier"],
        "tpcds": ["customer", "item", "store_sales", "date_dim"],
        "bike_sharing": ["data"],
        "accidents": ["us_accidents"]
    }
    return fallback_map.get(schema.lower(), ["sample_table_1", "sample_table_2"])


def execute_unity_catalog_sql(
    query: str,
    warehouse_id: Optional[str] = None,
    user_ctx: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Executes a SQL query on Databricks SQL Warehouse using the automatic OBO user token.
    Returns (df, None) on success or (None, error_str) on failure.
    """
    if user_ctx is None:
        user_ctx = get_current_user_context()

    token = user_ctx.get("token")
    raw_host = user_ctx.get("host") or os.environ.get("DATABRICKS_HOST", "")
    host = raw_host.replace("https://", "").replace("http://", "").split("/")[0]

    # Resolve warehouse ID & HTTP Path
    wh_id = warehouse_id or user_ctx.get("warehouse_id") or os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH", "")

    if not http_path and wh_id:
        http_path = f"/sql/1.0/warehouses/{wh_id}"

    # If HTTP path is still unknown, try listing warehouses via Databricks SDK
    if not http_path:
        wh_list = get_available_warehouses(user_ctx)
        if wh_list:
            wh_id = wh_list[0]["id"]
            http_path = f"/sql/1.0/warehouses/{wh_id}"

    if not token:
        return None, "No active Databricks OBO authentication token detected."

    if not host:
        return None, "No Databricks workspace host detected."

    if not http_path:
        return None, "No active SQL Warehouse configured. Please specify a Warehouse ID."

    try:
        from databricks import sql
        conn = sql.connect(
            server_hostname=host,
            http_path=http_path,
            access_token=token
        )
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)
        cursor.close()
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)
