import os
from flask import Flask, render_template, session
from google.cloud import datastore
import firebase_admin
from firebase_admin import credentials, firestore, auth
import logging 

#flask startup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '12345')

#logging configuration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#cloud datastore startup

datastore_client = datastore.Client()

#firebase initialising

try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(Cred)
    db = firestore.client()
    logger.ingo("Firebase initialised successfully")
except Exception as e:
    logger.error(f"Firebase initialisation failed")
    db = None

#importing routes

from app.routes import auth_routes, product_routes, order_routes, admin_routes

app.register_blueprint(auth_routes.bp)
app.register_blueprint(product_routes.bp)
app.register_blueprint(order_routes)
app.register_blueprint(admin_routes.bp)

@app.route
def home_page():
    '''home page'''
    return render_template('index.html')

@app.route('/health')
def check_health():
    '''endpoint health check'''
    return {'status': 'healthy', 'service': 'cloudmart'}

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"server error: {e}")

if __name__ == '__main__':

    app.run(host='127.0.0.1', port = 8080, debug= True)
    
