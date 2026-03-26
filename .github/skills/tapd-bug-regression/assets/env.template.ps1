# Copy to local.env.ps1 and fill with your own credentials.
# Never commit local.env.ps1.

$env:TAPD_API_TOKEN = "replace-with-your-own-token"
$env:TAPD_API_USER = "replace-with-your-own-user"
$env:TAPD_API_PASSWORD = "replace-with-your-own-password"

# Optional defaults
$env:TAPD_API_BASE_URL = "https://api.tapd.cn"
$env:TAPD_COMPANY_ID = "66514098"

# Optional: TAPD web upload bridge settings
$env:TAPD_WEB_BASE_URL = "https://www.tapd.cn"
$env:TAPD_WEB_STORAGE_STATE = ""
