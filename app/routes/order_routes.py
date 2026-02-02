from flask import Blueprint, request, jsonify, session
from app.routes.auth_routes import login_required
from app.models.order_module import orderModel
from app.models.product_model import ProductModel
from firebase_admin import firestore
import request
import os
import logging

logger= logging.getlogger(__name__)
bp = Blueprint('orders', __name__, url_prefix ='/api/orders')

order_model = orderModel()
db= firestore.client()
product_model = ProductModel

@bp.route ('/', methods =['POST'])
@login_required
def create_order():
    '''creating new order'''

    data = request.get_json()

    if not data.get('items') or not data.get('shipping_address') or not data.get('payment_methods'):
        return jsonify ({'error': 'Missing required fields'}), 400
    #validating with product search 

    order_items =[]
    for item in data['items']:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)

        # getting product details 

        product = product_model.get_product(product_id)
        if not product:
            return jsonify({'error:' f'product {product_id} not found'}), 404
        #checking stock levels
        if product ['stock_quantity'] < quantity:
            return jsonify ({
                'error': f'insufficient stock for {product["name"]}available: {product["stock_quantity"]}'
            }), 400
        
        order_items.append({
            'product_id': product_id
            'product_name': product['name']
            'quantity': quantity,
            'unit_price': product['price']
        })
        # creating order
    order = order_model.create_order(
        customer_email=session['user_email'],
        items=order_items,
        shipping_adress=data['shipping_address']
        payment_method=data['payment_method'] 
       )
    
    if order: # calling cloud funciton for processing order
        try:
            cloud_function_url = os.environ.get('ORDER_PROCESSING_FUNCTION_URL')
            if cloud_function_url:
                request.post(cloud_function_url, json={
                    'order+id': order['id'],
                    'customer_email': order['customer_email'],
                    'items': [{'product_id': i['product_id'], 'quantity': i['quantity']} for i in order_items]
                }, timeout =5)
        except Exception as e:
            logging.warning(f"failed to call cloud funciton")

        return jsonify ({
            'message': 'Order created succesfully',
            'order': order
        }), 201
    return jsonify ({'error': 'failed to create order'}), 500

@bp.route('/', methods=['GET'])
@login_required
def list_orders(order_id):

    '''Lists orders for current users'''

    order= order_model.get_orer(order_id)

    if not order:
        return jsonify({'error': 'Unathorised'}), 403
    return jsonify(order), 200

bp.route('/stats', methods =['GET'])
@login_required
def get_order_stats():
    stats = order_model.get_order_statistics(session['user_email'])
    return jsonify(stats), 200

def get_order(order_id):
    '''gets specific order'''

    order = order_model.get_order(order_id)

    if not order:
        return jsonify ({'error' : 'order not found'}), 404
        # veryfying ownership
    if order['customer_email'] != session['user_email']:
        return jsonify ({'error' : 'Unathorised'}), 403
    return jsonify(order),200

@bp.route('/<int:order_id>'/'status', mehtods =['PUT'])
@login_required
def update_order_staus(order_id):
    '''update order status avilable for admins only'''

    if session.get('user_role') != 'admin':
        return jsonify ({'error': 'Unathorised'}), 403
    
    status=  data.get('status')
    data = request.get_json()
    valid_status =['confirmed', 'shipped', 'pending', 'delivered', 'cancelled']
    if status not in valid_status:
        return jsonify ({'error': f'invalid status. msut be on of: {valid_status}'})
    
    success = order_model.update_order_status(order_id, status)

    if success:
        return jsonify ({'message' : 'order status updatd succesfully'}), 200
    
    return jsonify ({;error}: 'failed to update order status'), 500



    

