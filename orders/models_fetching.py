import os
import logging
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2 import service_account
from django.core.cache import cache

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPREADSHEET_ID = "1uXF3d9sXBKtiFPRR9efKlCsAz3kKzfqa7G67LXpIZi0"
RANGE_NAME = 'Sheet1!A1:A20'

SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "models-fetching",
    "private_key_id": "bad2d205e4884af3f4f37c31b2aff3c2a3a21bc2",
    "private_key": """-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCntSRoaZDxFa+C
    EVuTj+T9/55kkiBrbqIPBaonaTRBFnN9Loux7Hc+0CfL3OZwT1/nLiQ9P/v8uRfp
    GH5w88m17a6fASjJAtXrmyMEdIyAi9/gyDXghkMYHJHu18Sh31YC3drTPIvAYdPZ
    FseykeBh51u0O93ROwbeiK1/e6yUzd3Mu501AgBzx/+LEVEZojblUKmmT7ZF/wLg
    1EUu+DhqveCj/sTo1DPdfyGOcquX4fOcWdfHFcPKEIz6fr694FddL4pZqEIuBP9k
    wdysrnzhIJCAbLAv6hKc4ehcmZ3k2f6Xn2cQhYoFW77CngZL+IcftgRTaBmTHaEt
    GA7nn17tAgMBAAECggEACLF/hT7dQChrN22fttLhgFEjbGJh9jx/GUXZf78YvrvJ
    //xm48tpx89eelc/Er9Q+owOKnNwpBvfVqC20GZ/iqpOQCvKA3F3Yuxg/YNVIF/s
    mpuGP3DcqLLo1aqvPkmnc1dj8OM7xoMyFuS/zhl47VpJPkFQ/d5dCTGoj+n6ewdQ
    L3UptlT7sLIaLFDkjjD2oPUeA4fa1sNHyzUegVuZhv2s0rOIvD/Yv5TJeJ7EMWKH
    hdYx3kPyLOxwg8qATcsXXNzNsTQg3CBvypAM+ryx3DSSLg2V53O7zL6kU5gTll83
    0ytYb259k0mk50HfT9WPfnPikvQFe/g0AzeTBE/m+QKBgQDXVwbMXYIZanBoJw3p
    hZNyQdbOSnSkxVN1IQm/dOXODt4o4E81nL8iOQx8bHv/FMc5ItHef4NE5TzmxltY
    LxSccTvdH26jBhA/YhNP2KmACH8KzNTfilONPsyTQ7aGzlrTRQrwuyRZZ9izz0We
    hCxp3K0znb6+hZpOAIkzxXO/gwKBgQDHX7Dt/1sYy7douo/70+fSkgM0BO9L14/X
    SkmIw/Nkd3v11FuYWzM6BB/5smNtSr5sjxqzCwevv+LStOu4Zw2nsbv2M6rkbzSg
    zEldvyAKbtQaOgvOdWre6jZojS0uiPo54eEk81jLcZfEMtPECd05vtihacc5WqvO
    vdiBrd8szwKBgDiI+pnw+tUdYsGVb0ud7CYVLwYd+h3ASLb5o4uGb0b4FE97BJC4
    xF2ByMtp1+wSUnOntp3JsHcIEEMuVJEEW07vU54sQGnAj8d0Qkm2QloA4Qm+2SyP
    LnxovmDzaBpgVuwctlCZcWOfpf8fLdH+NYLdkwN4KLnwbaCI93yGHGttAoGAHFZy
    jHFmHlEeQYl6251T7u8H+4XUCWCbNkt9xi2r05TUDq3fUvlrf4yEivYbAbbE+CMi
    9V3U+tr4P2CtvGkRXMt7XtQbLxrLTSucJfH7eOAlz5B+ixrPVN3PW+7tBBc+EaoU
    WS8paMk9fAqJZOzN/94rZk3lnjZQAzOiqVPwS6sCgYBRbSTW7T2hUuFH8bioZBu4
    RVUnR0Jpch3c0vpHmTS9oMwrRSmcmDLaVKnEq/JCbyiebfiLwiCLZiyD363I56ga
    bkMENgYvCLhq3NjzSq5woD9FS9c1FeqxvdaudczMREkDjX61C6AHTnMZSABJKphR
    uWzXpf+Xo+YoIUXoGRn2sg==\n-----END PRIVATE KEY-----\n""",
    "client_email": "sheets-api-access@models-fetching.iam.gserviceaccount.com",
    "client_id": "115613619738814801268",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sheets-api-access%40models-fetching.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def authenticate_gsheets():
    try:
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        logger.error("Error authenticating with Google Sheets API: %s", e)
        raise

def get_models():
    try:
        cached_models = cache.get('models_cache')
        if cached_models:
            return cached_models

        service = authenticate_gsheets()
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        models = [row[0] for row in result.get('values', [])] if result.get('values', []) else []
        cache.set('models_cache', models, timeout=3600)
        return models
    except Exception as e:
        logger.error("Error fetching models from Google Sheets: %s", e)
        raise

if __name__ == '__main__':
    try:
        models = get_models()
        print(models)
    except Exception as e:
        logger.error("Failed to get models: %s", e)
