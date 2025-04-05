# app.py
import os
import json
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flasgger import Swagger
import base64
from bs4 import BeautifulSoup
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Load OpenAPI specification
with open('openapi.json', 'r') as f:
    swagger_config = json.load(f)

swagger = Swagger(app, template=swagger_config)

# eBay API configuration
EBAY_APP_ID = os.environ.get('KhoaNgoT-Applicat-SBX-3f7536b3f-b7ef7691')
EBAY_CLIENT_SECRET = os.environ.get('SBX-f7536b3fdc5b-a74e-4ff6-94b3-e86d')
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
        # Convert expires_in (in seconds) to epoch time and subtract 5 minutes for safety
        token_expiry = now + response_data['expires_in'] - (5 * 60)
        
        return access_token
    except Exception as e:
        app.logger.error(f'Error getting eBay token: {str(e)}')
        raise Exception('Failed to authenticate with eBay API')

@app.route('/search', methods=['GET'])
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
        limit = request.args.get('limit', default=5, type=int)
        
        if not q:
            return jsonify({'error': 'Search query is required'}), 400
        
        token = get_ebay_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        params = {
            'q': q,
            'limit': limit
        }
        
        response = requests.get(EBAY_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        error_details = e.response.json() if hasattr(e, 'response') and e.response else None
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500
        
        return jsonify({
            'error': 'Error searching eBay products',
            'details': error_details or error_message
        }), status_code
    except Exception as e:
        app.logger.error(f'Error searching products: {str(e)}')
        return jsonify({
            'error': 'Error searching eBay products',
            'details': str(e)
        }), 500

@app.route('/item', methods=['GET'])
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
            return jsonify({'error': 'Item ID is required'}), 400
        
        token = get_ebay_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        response = requests.get(f'{EBAY_ITEM_URL}{item_id}', headers=headers)
        response.raise_for_status()
        
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        error_details = e.response.json() if hasattr(e, 'response') and e.response else None
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500
        
        return jsonify({
            'error': 'Error getting eBay item details',
            'details': error_details or error_message
        }), status_code
    except Exception as e:
        app.logger.error(f'Error getting item details: {str(e)}')
        return jsonify({
            'error': 'Error getting eBay item details',
            'details': str(e)
        }), 500

@app.route('/category', methods=['GET'])
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
            return jsonify({'error': 'Query is required'}), 400
        
        token = get_ebay_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        params = {
            'q': q
        }
        
        response = requests.get(EBAY_CATEGORY_URL, headers=headers, params=params)
        response.raise_for_status()
        
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        error_details = e.response.json() if hasattr(e, 'response') and e.response else None
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500
        
        return jsonify({
            'error': 'Error suggesting eBay category',
            'details': error_details or error_message
        }), status_code
    except Exception as e:
        app.logger.error(f'Error suggesting category: {str(e)}')
        return jsonify({
            'error': 'Error suggesting eBay category',
            'details': str(e)
        }), 500

@app.route('/analyze-listing', methods=['POST'])
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
            return jsonify({"error": "Missing URL"}), 400

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return jsonify({"error": "Listing URL not available or removed"}), 400

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h1")
        desc_div = soup.find("div", id="desc_div") or soup.find("div", id="viTabs_0_is")
        
        raw_title = title.get_text(strip=True) if title else "No title found"
        raw_description = desc_div.get_text(strip=True) if desc_div else "No description available"

        words = re.findall(r'\b[a-zA-Z]{3,}\b', (raw_title + " " + raw_description).lower())
        keywords = sorted(set(words))

        return jsonify({
            "title": raw_title,
            "keywords": keywords[:20],
            "description_snippet": raw_description[:250]
        })

    except Exception as e:
        app.logger.error(f"Error analyzing listing URL: {str(e)}")
        return jsonify({"error": "Server error", "details": str(e)}), 500
        
        # Analyze title length (should be between 30-80 characters for optimal visibility)
        title_length = len(title)
        if title_length < 30:
            score += 20
            tips.append("Title is too short. Consider adding more relevant keywords to improve searchability.")
        elif title_length < 60:
            score += 40
            tips.append("Title is good but could be more descriptive to maximize keywords.")
        else:
            score += 50
            tips.append("Title length is excellent for eBay search optimization.")
        
        # Check for specific keywords in title
        if re.search(r'\b(new|brand new|sealed|unused)\b', title.lower()):
            score += 10
            tips.append("Good job including condition keywords in your title.")
        else:
            tips.append("Consider adding condition keywords to your title if applicable.")
        
        # Analyze price (this is a simplified example)
        # For a real implementation, you might want to compare with market prices
        if price > 0 and price < 1000:
            score += 20
            tips.append("Price point seems reasonable for most categories.")
        elif price >= 1000:
            score += 15
            tips.append("Higher priced items may need more detailed descriptions and photos.")
        
        # Add category-specific analysis if category is provided
        if category:
            score += 20
            # Additional category-specific analysis would go here
            tips.append(f"Listing is properly categorized in {category}.")
        else:
            tips.append("Adding a specific category can help buyers find your item.")
        
        # Cap the score at 100
        final_score = min(score, 100)
        
        # Get score rating
        if final_score >= 80:
            rating = "Excellent"
        elif final_score >= 60:
            rating = "Good"
        elif final_score >= 40:
            rating = "Fair"
        else:
            rating = "Poor"
        
        # Additional market advice
        market_advice = "Based on current eBay trends, consider adding free shipping to increase visibility."
        
        result = {
            "score": final_score,
            "rating": rating,
            "improvement_tips": tips,
            "market_advice": market_advice
        }
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f'Error analyzing listing: {str(e)}')
        return jsonify({
            'error': 'Error analyzing listing',
            'details': str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)