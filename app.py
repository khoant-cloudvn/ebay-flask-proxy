import os
import json
import time
import requests
import logging
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flasgger import Swagger
import base64
from bs4 import BeautifulSoup
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from services.ebay_service import EbayService
from utils.error_handlers import (
    EbayApiError, ValidationError,
    handle_ebay_api_error, handle_validation_error,
    handle_not_found, handle_server_error
)

# Configure logging
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Helper functions
def create_error_response(error_message, details=None, status_code=500):
    """Create a standardized error response"""
    response = {'error': error_message}
    if details:
        response['details'] = details
    return jsonify(response), status_code

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.RATE_LIMIT]
)

# Load OpenAPI specification
try:
    with open('openapi.json', 'r') as f:
        swagger_config = json.load(f)
    swagger = Swagger(app, template=swagger_config)
    logger.info("Swagger initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Swagger: {str(e)}")
    raise

# Initialize eBay service
ebay_service = EbayService()

# eBay API configuration
EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
EBAY_CLIENT_SECRET = os.environ.get('EBAY_CLIENT_SECRET')
EBAY_OAUTH_URL = 'https://api.ebay.com/identity/v1/oauth2/token'
EBAY_SEARCH_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
EBAY_ITEM_URL = 'https://api.ebay.com/buy/browse/v1/item/'
EBAY_CATEGORY_URL = 'https://api.ebay.com/commerce/taxonomy/v1/category_tree/0/get_category_suggestions'

# Token cache
access_token = None
token_expiry = 0

def get_ebay_token():
    """
    Get OAuth token from eBay API
    Returns a valid access token
    """
    global access_token, token_expiry
    now = time.time()
    
    if access_token and token_expiry > now:
        return access_token
    
    try:
        auth_string = f"{EBAY_APP_ID}:{EBAY_CLIENT_SECRET}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_auth}'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope'
        }
        
        response = requests.post(EBAY_OAUTH_URL, headers=headers, data=data)
        response.raise_for_status()
        
        response_data = response.json()
        access_token = response_data['access_token']
        token_expiry = now + response_data['expires_in'] - (5 * 60)
        
        logger.info("Successfully retrieved eBay OAuth token")
        return access_token
    except Exception as e:
        logger.error(f'Error getting eBay token: {str(e)}')
        raise Exception('Failed to authenticate with eBay API')

@app.route('/search', methods=['GET'])
@limiter.limit("30 per minute")
def search_products():
    """
    Search eBay products
    ---
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query
      - name: limit
        in: query
        type: integer
        required: false
        description: Maximum number of results to return
        default: 5
    responses:
      200:
        description: eBay search results
      400:
        description: Bad request
      500:
        description: Server error
    """
    try:
        q = request.args.get('q')
        limit = request.args.get('limit', default=Config.DEFAULT_SEARCH_LIMIT, type=int)
        
        if not q:
            raise ValidationError('Search query is required')
        
        results = ebay_service.search_products(q, limit)
        logger.info(f"Search query '{q}' returned {len(results.get('items', []))} results")
        return jsonify(results)
    except ValidationError as e:
        return handle_validation_error(e)
    except EbayApiError as e:
        return handle_ebay_api_error(e)
    except Exception as e:
        logger.error(f'Error searching products: {str(e)}')
        return handle_server_error(e)

@app.route('/item', methods=['GET'])
@limiter.limit("30 per minute")
def get_item_details():
    """
    Get item details by item ID
    ---
    parameters:
      - name: id
        in: query
        type: string
        required: true
        description: eBay item ID
    responses:
      200:
        description: eBay item detail
      400:
        description: Bad request
      500:
        description: Server error
    """
    try:
        item_id = request.args.get('id')
        
        if not item_id:
            raise ValidationError('Item ID is required')
        
        details = ebay_service.get_item_details(item_id)
        logger.info(f"Retrieved details for item ID {item_id}")
        return jsonify(details)
    except ValidationError as e:
        return handle_validation_error(e)
    except EbayApiError as e:
        return handle_ebay_api_error(e)
    except Exception as e:
        logger.error(f'Error getting item details: {str(e)}')
        return handle_server_error(e)

@app.route('/category', methods=['GET'])
@limiter.limit("30 per minute")
def suggest_category():
    """
    Suggest category based on keyword
    ---
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Category keyword
    responses:
      200:
        description: eBay category suggestion
      400:
        description: Bad request
      500:
        description: Server error
    """
    try:
        q = request.args.get('q')
        
        if not q:
            raise ValidationError('Query is required')
        
        suggestions = ebay_service.suggest_category(q)
        logger.info(f"Category suggestions generated for query '{q}'")
        return jsonify(suggestions)
    except ValidationError as e:
        return handle_validation_error(e)
    except EbayApiError as e:
        return handle_ebay_api_error(e)
    except Exception as e:
        logger.error(f'Error suggesting category: {str(e)}')
        return handle_server_error(e)

@app.route('/analyze-listing', methods=['POST'])
@limiter.limit("20 per minute")
def analyze_listing():
    """
    Analyze an eBay listing URL and extract title, keywords, and snippet.
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              url:
                type: string
                description: eBay listing URL
            required:
              - url
    responses:
      200:
        description: Extracted listing data
      400:
        description: Invalid input or listing URL
      500:
        description: Server error
    """
    try:
        data = request.get_json()
        url = data.get("url")
        
        if not url:
            raise ValidationError("Missing URL")
        if not re.match(r'^https?://(www\.)?ebay\.com/itm/', url):
            raise ValidationError("Invalid eBay listing URL")

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            raise ValidationError("Listing URL not available or removed")

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h1")
        desc_div = soup.find("div", id="desc_div") or soup.find("div", id="viTabs_0_is")
        
        raw_title = title.get_text(strip=True) if title else "No title found"
        raw_description = desc_div.get_text(strip=True) if desc_div else "No description available"

        words = re.findall(r'\b[a-zA-Z]{3,}\b', (raw_title + " " + raw_description).lower())
        keywords = sorted(set(words))

        result = {
            "title": raw_title,
            "keywords": keywords[:20],
            "description_snippet": raw_description[:250]
        }
        logger.info(f"Analyzed listing URL: {url}")
        return jsonify(result)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Error analyzing listing URL: {str(e)}")
        return handle_server_error(e)

# Register error handlers
app.register_error_handler(404, handle_not_found)
app.register_error_handler(500, handle_server_error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)

# Alias for Gunicorn compatibility
your_application = app
