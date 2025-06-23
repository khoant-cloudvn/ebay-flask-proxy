import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask settings
    DEBUG = False
    PORT = int(os.environ.get('PORT', 5000))
    
    # eBay API settings
    EBAY_APP_ID = os.environ.get('KhoaNgoT-Applicat-SBX-3f7536b3f-b7ef7691')
    EBAY_CLIENT_SECRET = os.environ.get('SBX-f7536b3fdc5b-a74e-4ff6-94b3-e86d')
    EBAY_OAUTH_URL = 'https://api.ebay.com/identity/v1/oauth2/token'
    EBAY_SEARCH_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
    EBAY_ITEM_URL = 'https://api.ebay.com/buy/browse/v1/item/'
    EBAY_CATEGORY_URL = 'https://api.ebay.com/commerce/taxonomy/v1/category_tree/0/get_category_suggestions'
    
    # API settings
    DEFAULT_SEARCH_LIMIT = 5
    TOKEN_EXPIRY_BUFFER = 5 * 60  # 5 minutes in seconds
    
    # Security settings
    RATE_LIMIT = '100 per minute'
    CORS_ORIGINS = ['*']  # Configure this based on your needs 