import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask settings
    DEBUG = False
    PORT = int(os.environ.get('PORT', 5000))
    
    # eBay API settings
    EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
    EBAY_CLIENT_SECRET = os.environ.get('EBAY_CLIENT_SECRET')
    EBAY_OAUTH_URL = 'https://api.ebay.com/identity/v1/oauth2/token'
    EBAY_SEARCH_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
    EBAY_ITEM_URL = 'https://api.ebay.com/buy/browse/v1/item/'
    EBAY_CATEGORY_URL = 'https://api.ebay.com/commerce/taxonomy/v1/category_tree/0/get_category_suggestions'
    
    # API settings
    DEFAULT_SEARCH_LIMIT = 5
    TOKEN_EXPIRY_BUFFER = 5 * 60  # 5 minutes in seconds
    
    # Security settings
    RATE_LIMIT = '100 per minute'
    CORS_ORIGINS = ['https://chat.openai.com']  # Update to your GPT's domain in production
