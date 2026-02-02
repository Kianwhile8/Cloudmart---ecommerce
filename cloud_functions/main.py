'''cloud funcitons for order proccessing and analytics'''


import functions_framework
from google.cloud import firestore
import logging

db = firestore.Client

logger = logging.getLogger(__name__)

@functions_framework.http
def order_process(request):

    '''http cloud funciton to process orders
    triggered after order creation'''

    if request.method =='OPTIONS':
        headers = {
            'Access-Control-Allow-Oriign': '*',
            'Access-Contorl-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)
    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        request_json = request.get_json(silent=True)

        if not request_json:
            return {'error': 'Invalid JSON'}, 400, headers
        order_id = request_json.get('order_id')
        customer_email = request_json.get('customer_email')
        items = request_json.get('items', [])

        if not order_id or not customer_email:
            return {'error': 'Missing required fields'}, 400, headers
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity',0)

            if product_id:
                try:
                    product_ref = db.collection('products').document(product_id)
                    product_ref.update({
                        'quantity': firestore.Increment (-quantity),
                        'sales': firestore.Increment (quantity)
                    })
                    logger.info(f"updated inventory for product {product_id}")
                except Exception as e:
                    logger.error(f"failed to update product {product_id}: {e}")

                    #can add confirmation email or notifcations to customers here

            return {
                    'success': True,
                    'message': 'order processed successfully',
                    'order_id': order_id
            }, 200, headers
    except Exception as e:
        logger.error(f"error processing order: {e}")
        return{'error': str(e)}, 500, headers
    
@functions_framework.http
def create_analytics(request):
    '''generates analytics'''
    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        products = db.collection('products').stream()

        analytics = {
            'total_products': 0,
            'total_sales': 0,
            'top_products' : [],
            'total_revenue': 0.0,
            'categories':{}
        }
        product_list =[]

        for product in products:
            product_data = product.to_dict()
            analytics['total_products'] += 1

            sales_count = product_data.get('sales', 0)
            price = product_data.get('price', 0)

            analytics['total_sales'] += sales_count
            analytics ['total_revenue'] += sales_count * price

            #tracking by category

            category = product_data.get('category', 'other')
            if category not in analytics['categories']:
                analytics['categories'][category] ={
                    'sales': 0,
                    'revenue': 0.0
                }
            analytics['categories'][category]['revenue'] += sales_count *price
            analytics['categories'][category]['sales'] +=sales_count

                #top product data collection
            product_list.append({
                'id': product.id,
                'sales' : sales_count,
                'name': product_data.get('name'),
                'revenue': sales_count *price
            })

        #top 10 best selling products

        product_list.sort(key=lambda x: x['sales'], reverse=True)
        analytics['top_products'] = product_list [:10]

        return analytics, 200, headers
    except Exception as e:
        logger.error(f"error generating analytics: {e}")
        return {'error': str(e)}, 500, headers
        

