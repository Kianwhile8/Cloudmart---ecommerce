from flask import Blueprint, request, jsonify, session
from firebase_admin import firestore
from app.models.product_model import ProductModel
from app.routes.auth_routes import login_required, role_required
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('products', __name__, url_prefix='/api/products')

db = firestore.client()
product_model = ProductModel(db)

@bp.route('/', methods = ['GET'])
def list_products():
    '''list all products with optional filters'''

    filters = {}

    if request.args.get('category'):
        filters ['category'] = request.args.get('category')
    if request.args.get('vendor_email'):
        filters ['vendor_email'] = request.args.get('vendor_email')
    if request.args.get('min_price'):
        filters ['min_price'] = float(request.args.get('min_price'))
    if request.args.get('max_price'):
        filters ['max_price'] = float(request.args.get('max_price'))
    
    limit = int(request.args.get('lmit,', 50))

    products = product_model.list_products(filters=filters if filter else None, limit = limit)
    return jsonify(products), 200

@bp.route('<product_id>', methods=['GET'])
def get_product(product_id):

    '''gets a single product by ID'''

    product= product_model.get_product(product_id)
    if product: # iincreasing view count
        product_model.view_increase(product_id)
        return jsonify(product), 200
    
    return jsonify ({'error': 'product not found'}), 404 

@bp.route('/', methods = ['POST'])
@login_required
@role_required('vendor')
def create_product():
    '''creates new product'''

    data  = request.get_json()
    required = ['name', 'description', 'price', 'category', 'quantity']
    if not all (field in data for field in required):
        return jsonify ({'error': 'missing required fields'}), 400
    
    #adding vendor email from current session

    data['vendor_email'] = session ['user_email']

    #validating data types

    try:
        data['price'] = float(data['price'])
        data['quantity'] = int(data['stock_quantity'])
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid price or stock quantity'}), 400
    
    product_id = product_model.create_product(data)

    if product_id:
        return jsonify({
            'message' : 'product succesfully created',
            'product_id': product_id
        }),201
    return jsonify({'error': 'fialed to create product'}), 500

@bp.route('/<product_id>', methods = ['PUT'])
@login_required
@role_required('vendor')
def update_product(product_id):
    '''updates product'''

    product = product_model.get_product(product_id)
    if product ['vendor_email'] != session ['user_email']:
        return jsonify ({'error': 'Unauthorised'}), 403
    
    if not product:
        return jsonify({'error': 'product not found'}), 404

    data = request.get_json()

    #removing fields that shouldnt be updated

    data.pop('vendor_email', None)
    data.pop ('created_at', None)
    data.pop('id', None)

    success = product_model.update_product(product_id. data)

    if success:
        return jsonify({'message': 'Product updated succesfully'}), 200
    return jsonify({'error': 'Failed to update product'}), 500

@bp.route('/<product_id', methods= ['DELETE'])
@login_required
@role_required('vendor')

def delete_product(product_id):
    '''allows vendors to delete products'''
    #verifying ownership
    product = product_model.get_product(product_id)

    if not product:
        return jsonify({'error': 'product not found'})
    
    if product['vendor_email'] != session ['user_email']:
        return jsonify({'error' : 'Unatuhorised'})
    success = product_model.delete_product(product_id)

    if success:
        return jsonify({'message': 'product deleted sucesfully'}), 200
    return jsonify ({'error' : 'failed to delete product'}),500

@bp.route('search', methods =['GET'])
def search_products():
    '''search products by name or description'''

    search_term = request.args.get('q', '')

    if not search_term:
        return jsonify({'error', 'search term required'}), 400
    
    results = product_model.search_products(search_term)
    return jsonify(results), 200
@bp.route('/categories', methods= ['GET'])

def get_categories():
    '''gets list of all product categories'''

    products = product_model.list_products(limit=1000)
    categories = list(set(p.get('category', 'Other') for p in products))
    categories.sort()

    return jsonify({'categories': categories}), 200



    