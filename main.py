import os
from flask import Flask, render_template, session
from google.cloud import datastore
import firebase_admin
from firebase_admin import credentials, firestore, auth
import logging 
from datetime import timedelta

#flask startup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '12345')
app.config ['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

#logging configuration

logging.basicConfig(
    level=logging.INFO,
    format= '%(asctime)s - %(name)s - %(levelname)s - %(messages)s'
)
logger=logging.getLogger(__name__)

#cloud datastore startup

try:
    datastore_client = datastore.Client()
    logger.info("cloud datastore initisalised successfully")
except Exception as e:
    logger.warning (f"cloud datastore intialisation failed: {e}")
    logger.warning(f"running in devlopment mode without GCP")


#firebase initialising

try:
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(Cred)
    db = firestore.client()
    logger.info("Firebase initialised successfully")
except Exception as e:
    logger.error(f"Firebase initialisation failed {e}")
    logger.warning("running in devlopment mode without firebase")
    db = None

#importing routes

from app.routes import auth_routes, product_routes, order_routes, admin_routes

app.register_blueprint(auth_routes.bp)
app.register_blueprint(product_routes.bp)
app.register_blueprint(order_routes)
app.register_blueprint(admin_routes.bp)

@app.route('/')
def home_page():
    '''home page'''
    return render_template('index.html')

@app.route('/health')
def check_health():
    '''endpoint health check'''
    return {'status': 'healthy',
            'service': 'cloudmart'
        }, 200

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"server error: {e}")

@app.context_processor
def user_injection():
    '''injecting session data from user into all templates'''
    return dict(
        user_email=session.get('user_email')
        user_role=session.get('user_role')
        user_name=session.get('user_name'),
    )

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 8080))
    app.run(host='127.0.0.1', port = 8080, debug= True)
    
