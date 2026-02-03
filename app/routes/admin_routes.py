''' admin routes
allows admin functions for admin role'''

from flask import Blueprint, request, jsonify, render_template
from app.routes.auth_routes import required_login, role_required
from app.models.user_model import UserModel
from app.models.order_model import OrderModel
from app.models.product_model import ProductModel
from google.cloud import datastore
from firebase_admin import firestore
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('admin', __name__, url_prefix ='/admin')

datastore_client = datastore.client()
user_model = UserModel(datastore_client)
order_model = OrderModel()
db = firestore.client()
product_model = ProductModel(db)

@bp.route('/')
@required_login
@role_required('admin')

def admin_dashboard():

    return render_template ('admin/dashboard.html')

@bp.route ('/api/dashboard', methods =['GET'])
@required_login
@role_required
def get_dashboard_data ():
    '''gets dashboard statistics''' 
    #user statistics

    users= user_model.list_users()
    user_stats ={
        'total_users': len(users),
        'customers': len([u for u in users if u['role'] == 'customer']),
        'vendors' : len([ u for u in users if u ['role'] =='vendor ']),
        'admins': len([u for u in users if u ['role'] == 'admin'])
    }
# product statistics 

    products = product_model.list_products(limit = 1000)
    product_stats = {
        'total_products': len(products),
        'active' : len([p for p in products if p.get('active', True)]),
        'total_views': sum(p.get('views',0) for p in products),
        'total_sales': sum(p.get('sales_count', 0)for p in products)
    }

#order statistics
    order_stats = order_model.get_order_statistics()

    return jsonify({
        'users': user_stats,
        'products': product_stats,
        'orders': order_stats
    }), 200

@bp.route('/api/users', methods =['GET'])
@required_login
@role_required('admin')
def list_all_users():

    '''lists all users'''
    users = request.args.get('role')
    role = user_model.list_users(role=role)
    
    for user in users:
        user.pop('password_hash', None)
    return jsonify(users), 200

@bp.route('api/users/<email>/role', methods =['PUT'])
@required_login
@role_required('admin')
def update_user_role(email):
    '''updates user roles'''
    data = request.get_json()
    new_role = data.get('role')

    valid_roles = ['customer', 'vendor', 'admin']
    if new_role not in valid_roles:
        return jsonify({'error': 'Invalid role specified.'}), 400
    user = user_model.update_user(email, role=new_role)

    if user:
        return jsonify({"message": 'User role updated successfully.'}), 200
    else:
        return jsonify({'error': 'User not found.'}), 404
    
@bp.route('/api/products', methods =['GET'])
@required_login 
@role_required('admin')
def list_all_products():
    '''creates a list of  all products'''
    limit = int(request.args.get('limit', 100))
    products = product_model.list_products(limit=limit)
    return jsonify(products), 200

@bp.route ('api/products/<product_id>/activate', methods =['PUT'])
@required_login
@role_required('admin')
def activate_product(product_id):
    '''activates a deactivated product'''
    product = product_model.update_product(product_id, active = True)
    if product:
        return jsonify({'message': 'Product activated successfully.'}), 200
    return jsonify({'error': 'Product not found.'}), 404
