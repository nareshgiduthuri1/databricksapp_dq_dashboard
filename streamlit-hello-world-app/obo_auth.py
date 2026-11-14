"""
Databricks On-Behalf-Of (OBO) Authentication Module for Project Allianz.

NO PERSONAL ACCESS TOKEN (PAT) IS REQUIRED!
Databricks Apps automatically generates and forwards an ephemeral OAuth user token
in the HTTP request header: 'X-Forwarded-Access-Token'.

When a user logs in via SSO, queries to Databricks SQL Warehouses execute On-Behalf-Of
that logged-in user, enforcing Unity Catalog Row-Level Security and Column Masking.
"""

import os
import re
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


def get_workspace_host() -> str:
    """
    Resolves the real Databricks workspace hostname (e.g. adb-3649210770249640.0.azuredatabricks.net).
    Crucial fix: Never use the app URL domain (which is only the web frontend container).
    """
    # 1. Try databricks.sdk.core Config
    try:
        from databricks.sdk.core import Config
        cfg = Config()
        if cfg.host:
            clean_host = cfg.host.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
            if "azure.databricksapps.com" not in clean_host and clean_host:
                return clean_host
    except Exception:
        pass

    # 2. Try DATABRICKS_HOST env var
    env_host = os.environ.get("DATABRICKS_HOST", "")
    if env_host:
        clean_env = env_host.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
        if "azure.databricksapps.com" not in clean_env and clean_env:
            return clean_env

    # 3. Automatically extract Azure Databricks Workspace ID from the App URL headers!
    # Example URL: data-quality-dashboard-3649210770249640.0.azure.databricksapps.com
    headers = get_obo_headers()
    app_host = headers.get("host", "")
    if "azure.databricksapps.com" in app_host:
        match = re.search(r"(\d+(\.\d+)?)\.azure\.databricksapps\.com", app_host)
        if match:
            ws_id = match.group(1)
            return f"adb-{ws_id}.azuredatabricks.net"

    # Default fallback workspace host
    return "adb-3649210770249640.0.azuredatabricks.net"


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
    
    host = get_workspace_host()
        
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    if not warehouse_id and st is not None and hasattr(st, "session_state") and "custom_wh_id" in st.session_state:
        warehouse_id = st.session_state["custom_wh_id"]
    
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
            "user_email": user_email or "naresh.giduthuri@allianz.com",
            "host": host,
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
        from databricks.sdk.core import Config
        if user_ctx is None:
            user_ctx = get_current_user_context()
        token = user_ctx.get("token")
        host = get_workspace_host()

        if token and host:
            # Databricks Apps ALSO injects DATABRICKS_CLIENT_ID / DATABRICKS_CLIENT_SECRET
            # (the app service principal). Passing token= alone makes the SDK fail with
            # "more than one authorization method configured: oauth and pat".
            # Pin auth_type="pat" so ONLY the logged-in user's OBO token is used.
            cfg = Config(host=f"https://{host}", token=token, auth_type="pat")
            return WorkspaceClient(config=cfg)
        # No user token -> fall back to the app service principal credentials
        return WorkspaceClient()
    except Exception as e:
        print(f"[obo_auth] WorkspaceClient init failed: {e}", flush=True)
        return None


def _friendly_auth_error(raw: str) -> str:
    """Turns the cryptic OBO scope error into an actionable message for the user."""
    if "required scopes" in raw:
        return (
            "Your sign-in token for this app was issued before the 'sql' permission was added, "
            "so it cannot run queries. Sign out of the app (or open it in a private/incognito window) "
            "and accept the permission prompt again to get a new token."
        )
    return raw


_NUMERIC_TYPES = {"BYTE", "SHORT", "INT", "LONG", "FLOAT", "DOUBLE", "DECIMAL"}


def _run_statement_sdk(w, warehouse_id: str, statement: str, timeout_s: int = 180) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Runs SQL through the Statement Execution API, polling until finished
    (covers warehouse cold starts), reading ALL result chunks, and converting
    the string-only JSON results back to proper numeric / date / boolean dtypes.
    """
    import time
    from databricks.sdk.service.sql import StatementState

    res = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="30s"
    )
    deadline = time.time() + timeout_s
    while res.status and res.status.state in (StatementState.PENDING, StatementState.RUNNING):
        if time.time() > deadline:
            return None, f"Query still running after {timeout_s}s (warehouse may be starting). Please retry."
        time.sleep(2)
        res = w.statement_execution.get_statement(res.statement_id)

    state = res.status.state if res.status else None
    if state != StatementState.SUCCEEDED:
        err = res.status.error.message if (res.status and res.status.error) else f"Statement ended in state {state}"
        return None, f"Databricks SQL error: {err}"

    columns = res.manifest.schema.columns if (res.manifest and res.manifest.schema) else []
    col_names = [c.name for c in columns]
    col_types = [(c.type_name.value if c.type_name else "STRING") for c in columns]

    rows = list(res.result.data_array or []) if res.result else []
    chunk = res.result
    while chunk is not None and chunk.next_chunk_index is not None:
        chunk = w.statement_execution.get_statement_result_chunk_n(res.statement_id, chunk.next_chunk_index)
        rows.extend(chunk.data_array or [])

    df = pd.DataFrame(rows, columns=col_names)
    for name, t in zip(col_names, col_types):
        if t in _NUMERIC_TYPES:
            df[name] = pd.to_numeric(df[name], errors="coerce")
        elif t in ("DATE", "TIMESTAMP", "TIMESTAMP_NTZ"):
            df[name] = pd.to_datetime(df[name], errors="coerce")
        elif t == "BOOLEAN":
            df[name] = df[name].map({"true": True, "false": False})
    return df, None


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
    # 1. Try Databricks SDK REST API
    try:
        w = get_workspace_client(user_ctx)
        if w:
            schemas = [s.name for s in w.schemas.list(catalog_name=catalog)]
            if schemas:
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

    # 3. Fallback for 'samples'
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

    fallback_map = {
        "nyctaxi": ["trips"],
        "tpch": ["customer", "orders", "lineitem", "nation", "part", "partsupp", "region", "supplier"],
        "tpcds": ["customer", "item", "store_sales", "date_dim"],
        "bike_sharing": ["data"],
        "accidents": ["us_accidents"]
    }
    return fallback_map.get(schema.lower(), ["sample_table_1", "sample_table_2"])


def test_warehouse_connection(warehouse_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Diagnostic tool: Runs a lightweight query (SELECT current_user()) to verify
    the connection and reports exact status/errors in plain English.
    """
    host = get_workspace_host()
    user_ctx = get_current_user_context()
    token = user_ctx.get("token")
    wh_id = warehouse_id or user_ctx.get("warehouse_id") or os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    
    clean_wh_id = wh_id.replace("/sql/1.0/warehouses/", "").strip()
    http_path = f"/sql/1.0/warehouses/{clean_wh_id}" if clean_wh_id else ""

    result = {
        "host": host,
        "token_detected": bool(token),
        "token_len": len(token) if token else 0,
        "warehouse_id": clean_wh_id,
        "http_path": http_path,
        "success": False,
        "message": ""
    }

    if not clean_wh_id:
        result["message"] = "SQL Warehouse ID is missing. Please enter your 16-character SQL Warehouse ID."
        return result

    # Test 1: databricks-sql-connector
    try:
        from databricks import sql
        conn = sql.connect(
            server_hostname=host,
            http_path=http_path,
            access_token=token
        )
        cursor = conn.cursor()
        cursor.execute("SELECT current_user() AS usr, current_timestamp() AS ts")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        result["success"] = True
        result["message"] = f"Connected successfully! Authenticated as: {row[0]} | Server Timestamp: {row[1]}"
        return result
    except Exception as e:
        err1 = str(e)

    # Test 2: databricks-sdk statement execution (with polling)
    try:
        w = get_workspace_client(user_ctx)
        if w:
            df, sdk_err = _run_statement_sdk(w, clean_wh_id, "SELECT current_user() AS usr, current_timestamp() AS ts")
            if df is not None and not df.empty:
                result["success"] = True
                result["message"] = f"Connected successfully via Databricks SDK! Authenticated as: {df.iloc[0, 0]}"
                return result
            err1 += f" | SDK: {sdk_err}"
        else:
            err1 += " | SDK: WorkspaceClient could not be created (see app logs)"
    except Exception as e2:
        err1 += f" | SDK execution notice: {e2}"

    result["message"] = err1
    return result


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
    host = get_workspace_host()

    wh_id = warehouse_id or user_ctx.get("warehouse_id") or os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    clean_wh_id = wh_id.replace("/sql/1.0/warehouses/", "").strip()
    http_path = f"/sql/1.0/warehouses/{clean_wh_id}" if clean_wh_id else ""

    if not clean_wh_id:
        return None, "SQL Warehouse ID is not configured. Please enter your Warehouse ID in the settings box."

    # 1. Try databricks-sql-connector
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
        err1 = str(e)

    # 2. Try databricks-sdk statement execution (polls, reads all chunks, restores dtypes)
    try:
        w = get_workspace_client(user_ctx)
        if w:
            df, sdk_err = _run_statement_sdk(w, clean_wh_id, query)
            if df is not None:
                return df, None
            print(f"[obo_auth] SQL failed. connector: {err1} | sdk: {sdk_err}", flush=True)
            return None, _friendly_auth_error(f"{sdk_err} (connector: {err1})")
    except Exception as e2:
        print(f"[obo_auth] SQL failed. connector: {err1} | sdk exception: {e2}", flush=True)
        if "required scopes" in str(e2):
            return None, _friendly_auth_error(str(e2))
        return None, f"{err1} (SDK: {e2})"

    return None, err1
