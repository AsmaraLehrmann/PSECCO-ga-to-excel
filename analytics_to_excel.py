import os
import json
from datetime import date, timedelta

import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient

# 1. GA4 service-account auth
ga_info = json.loads(os.environ["GA_CREDENTIALS_JSON"])
ga_creds = service_account.Credentials.from_service_account_info(ga_info)
ga_client = BetaAnalyticsDataClient(credentials=ga_creds)

today = date.today().replace(day=1)
start = (today - timedelta(days=1)).replace(day=1)
end   = today - timedelta(days=1)

response = ga_client.run_report(
    property=f"properties/{os.environ['GA4_PROPERTY_ID']}",
    date_ranges=[{"start_date": start.isoformat(), "end_date": end.isoformat()}],
    metrics=[{"name": "totalUsers"}]
)
users = int(response.rows[0].metric_values[0].value)
print(f"GA4: {users} users from {start} to {end}")

# 2. Microsoft Graph auth + append row
tenant_id     = os.environ["GRAPH_TENANT_ID"]
client_id     = os.environ["GRAPH_CLIENT_ID"]
client_secret = os.environ["GRAPH_CLIENT_SECRET"]
cred          = ClientSecretCredential(tenant_id, client_id, client_secret)
graph_client  = GraphClient(credential=cred, scopes=["https://graph.microsoft.com/.default"])

path      = os.environ["GRAPH_WORKBOOK_PATH"]  # e.g. "PSECCO/MonthlyStats.xlsx"
table     = os.environ.get("GRAPH_TABLE_NAME", "Table1")
drive_item = graph_client.get(f"/me/drive/root:/{path}:/").json()
item_id    = drive_item["id"]

row = [[ start.strftime("%Y-%m"), users ]]
graph_client.post(f"/me/drive/items/{item_id}/workbook/tables/{table}/rows/add",
                  json={"values": row})

print("✅ Appended row to Excel table")
