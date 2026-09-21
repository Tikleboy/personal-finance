import os
import json
import gspread
import time
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Cross-platform & Environment Variable Credential Loading
creds_json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")

if creds_json_env:
    info = json.loads(creds_json_env)
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_creds_path = os.path.join(base_dir, "credentials", "personal-finance-509304-61da427d86b8.json")
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", default_creds_path)
    credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

client = gspread.authorize(credentials)

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1OPuDbTWTVr6GpRTIjRY_vTd8mVDsH-lm2eq7-sIoqq8")

spreadsheet = client.open_by_key(SPREADSHEET_ID)

# In-Memory Cache Variables
_TRANSACTIONS_CACHE = None
_TRANSACTIONS_CACHE_TIME = 0
_CATEGORIES_CACHE = None
_CATEGORIES_CACHE_TIME = 0
CACHE_TTL_SECONDS = 60  # Cache duration: 60 seconds


# =========================
# SHEETS
# =========================

def get_transactions_sheet():
    return spreadsheet.worksheet("Transactions")


def get_categories_sheet():
    return spreadsheet.worksheet("Categories")


def get_budget_sheet():
    return spreadsheet.worksheet("Budget")


def get_savings_goals_sheet():
    return spreadsheet.worksheet("Savings Goals")


# =========================
# TRANSACTIONS
# =========================

def clear_cache():
    global _TRANSACTIONS_CACHE, _TRANSACTIONS_CACHE_TIME, _CATEGORIES_CACHE, _CATEGORIES_CACHE_TIME
    _TRANSACTIONS_CACHE = None
    _TRANSACTIONS_CACHE_TIME = 0
    _CATEGORIES_CACHE = None
    _CATEGORIES_CACHE_TIME = 0


def get_transactions():
    global _TRANSACTIONS_CACHE, _TRANSACTIONS_CACHE_TIME
    now = time.time()
    
    # Return cached data if available and fresh
    if _TRANSACTIONS_CACHE is not None and (now - _TRANSACTIONS_CACHE_TIME) < CACHE_TTL_SECONDS:
        return _TRANSACTIONS_CACHE

    sheet = get_transactions_sheet()
    _TRANSACTIONS_CACHE = sheet.get_all_records()
    _TRANSACTIONS_CACHE_TIME = now
    return _TRANSACTIONS_CACHE


def add_transaction(transaction):
    sheet = get_transactions_sheet()

    sheet.append_row([
        transaction["id"],
        transaction["date"],
        transaction["type"],
        transaction["category"],
        transaction["amount"],
        transaction["description"]
    ])
    
    # Invalidate cache so fresh data is fetched
    clear_cache()


def update_transaction(row_number, transaction):
    sheet = get_transactions_sheet()

    sheet.update(
        f"A{row_number}:F{row_number}",
        [[
            transaction["id"],
            transaction["date"],
            transaction["type"],
            transaction["category"],
            transaction["amount"],
            transaction["description"]
        ]]
    )
    
    # Invalidate cache
    clear_cache()


def delete_transaction(row_number):
    sheet = get_transactions_sheet()

    sheet.delete_rows(row_number)
    
    # Invalidate cache
    clear_cache()


# =========================
# CATEGORIES
# =========================

def get_categories():
    global _CATEGORIES_CACHE, _CATEGORIES_CACHE_TIME
    now = time.time()

    if _CATEGORIES_CACHE is not None and (now - _CATEGORIES_CACHE_TIME) < (CACHE_TTL_SECONDS * 5):
        return _CATEGORIES_CACHE

    sheet = get_categories_sheet()
    _CATEGORIES_CACHE = sheet.get_all_records()
    _CATEGORIES_CACHE_TIME = now
    return _CATEGORIES_CACHE