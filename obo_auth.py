"""
Databricks On-Behalf-Of (OBO) Authentication Module for Project Allianz.

NO PERSONAL ACCESS TOKEN (PAT) IS REQUIRED!
Databricks Apps automatically generates and forwards an ephemeral OAuth user token
in the HTTP request header: 'X-Forwarded-Access-Token'.

When a user logs in via SSO, queries to Databricks SQL Warehouses execute On-Behalf-Of
that logged-in user, enforcing Unity Catalog Row-Level Security and Column Masking.
"""

import os
from typing import Dict, Any, Optional
import streamlit as st


def get_obo_headers() -> Dict[str, str]:
    """
    Extracts HTTP headers injected automatically by Databricks Apps gateway.
    In Streamlit 1.35+, request headers are available in st.context.headers.
    """
    headers = {}
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
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
    obo_token = headers.get("x-forwarded-access-token") or headers.get("X-Forwarded-Access-Token")
    
    # 2. Databricks Apps automatically injects the user's corporate email / identity
    user_email = (
        headers.get("x-forwarded-email")
        or headers.get("X-Forwarded-Email")
        or headers.get("x-forwarded-user")
        or headers.get("X-Forwarded-User")
        or headers.get("x-forwarded-preferred-username")
        or headers.get("X-Forwarded-Preferred-Username")
    )
    
    # Databricks Apps automatically provides DATABRICKS_HOST in the container environment
    host = os.environ.get("DATABRICKS_HOST", "")
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    
    if obo_token:
        # ---------------------------------------------------------------------
        # RUNNING IN DATABRICKS APPS WITH LIVE OBO
        # No personal token or password required!
        # ---------------------------------------------------------------------
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
        # ---------------------------------------------------------------------
        # RUNNING LOCALLY ON LAPTOP (SIMULATION / DEMO MODE)
        # Because local laptop runs outside Databricks Apps gateway
        # ---------------------------------------------------------------------
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


def get_databricks_sql_connection(user_ctx: Dict[str, Any]):
    """
    Connects to Databricks SQL Warehouse using the automatic OBO user token.
    No service principal or personal access token needed.
    """
    token = user_ctx.get("token")
    raw_host = user_ctx.get("host") or os.environ.get("DATABRICKS_HOST", "")
    host = raw_host.replace("https://", "").replace("http://", "").split("/")[0]
    
    warehouse_id = user_ctx.get("warehouse_id") or os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH", f"/sql/1.0/warehouses/{warehouse_id}" if warehouse_id else "")
    
    if not token or not host or not http_path:
        return None
    
    try:
        from databricks import sql
        conn = sql.connect(
            server_hostname=host,
            http_path=http_path,
            access_token=token  # Ephemeral OBO token provided automatically by Databricks!
        )
        return conn
    except Exception as e:
        st.warning(f"Note: Databricks SQL connection notice: {e}. Utilizing cached governance metrics.")
        return None
