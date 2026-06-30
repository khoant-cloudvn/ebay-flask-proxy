from flask import jsonify

class EbayApiError(Exception):
    pass

class ValidationError(Exception):
    pass

def handle_ebay_api_error(e):
    return jsonify({'error': 'eBay API error', 'details': str(e)}), 502

def handle_validation_error(e):
    return jsonify({'error': 'Validation error', 'details': str(e)}), 400

def handle_not_found(e):
    return jsonify({'error': 'Not found'}), 404

def handle_server_error(e):
    return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
