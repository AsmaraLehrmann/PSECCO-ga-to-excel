import os
import json
from datetime import date, timedelta

import pandas as pd
import requests
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account
from azure.identity import ClientSecretCredential

# ─── 1. GA4 service‐account auth ───────────────────────────────────────────────
ga_info = json.loads(os.environ["GA_CREDENTIALS_JSON"])
ga_creds = service_account.Credentials.from_service_account_info(ga_info)
ga_client = BetaAnalyticsDataClient(credentials=ga_creds)

today = date.today().replace(day=1)
start = (today - timedelta(days=1)).replace(day=1)
end   = today - timedelta(days=1)

# → use the “request” dict instead of property=…
response = ga_client.run_report(request={
    "property": f"properties/{os.environ['GA4_PROPERTY_ID']}",
    "date_ranges": [{"start_date": start.isoformat(), "end_date": end.isoformat()}],
    "metrics": [{"name": "totalUsers"}]
})
users = int(response.rows[0].metric_values[0].value)
print(f"GA4: {users} users from {start} to {end}")

# ─── 2. Get an access token for Microsoft Graph ────────────────────────────────
tenant_id     = os.environ["GRAPH_TENANT_ID"]
client_id     = os.environ["GRAPH_CLIENT_ID"]
client_secret = os.environ["GRAPH_CLIENT_SECRET"]
credential    = ClientSecretCredential(tenant_id, client_id, client_secret)
token = credential.get_token("https://graph.microsoft.com/.default")
access_token = token.token

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# ─── 3. Find your workbook’s driveItem ID ──────────────────────────────────────
workbook_path = os.environ["GRAPH_WORKBOOK_PATH"]
url_meta = f"https://graph.microsoft.com/v1.0/me/drive/root:/{workbook_path}:"
r = requests.get(url_meta, headers=headers)
r.raise_for_status()
item_id = r.json()["id"]

# ─── 4. Append the row to your table ───────────────────────────────────────────
table_name = os.environ.get("GRAPH_TABLE_NAME", "Table1")
row = [[ start.strftime("%Y-%m"), users ]]
url_rows = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/workbook/tables/{table_name}/rows/add"
r2 = requests.post(url_rows, headers=headers, json={"values": row})
r2.raise_for_status()

print("✅ Appended row to Excel table")
