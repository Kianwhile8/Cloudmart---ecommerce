from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from functools import wraps
from app.models.user_model import UserModel
from google.cloud import datastore
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix = '/auth')

datastore_client = datastore.Client()
user_model = UserModel(datastore_client)

def required_login(f):
    '''checks if user is logged in. 
    if yes funciton allowed to run if no, redirected to login page'''

    @wraps(f)
    def dfunciton(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return dfunciton
    # checks if user is not logged in, if uers is logged in contineu

def required_role(role_required):
    '''require specific roles
    customer
    vendor
    admin
    '''

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_email' not in session:
                return redirect(url_for('auth.login_page'))
            
            if session.get("user_role") != role_required:

                return jsonify({'error': 'Unathorised'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('register', methods=['GET'])
def register_page():
    '''get /auth/register and display registration page'''
    return render_template('auth/register.html')

@bp.route('/register', methods=['post'])
def register():
    '''creates new user'''
    data = request.get_json() or request.form.to_dict()

    #validating inputs
    required_field = ['emial', 'password', 'name']
    if not all(field in data for field in required_field):
        return jsonify({'error': 'missing required fields: email, password, name'})
    
    email = data['email'].lower().strip()
    password = data['password']
    name = data['name'].strip()
    role = data.get('role', 'customer') # defaults to customer

    #validating roles
    valid_roles = ['customer', 'vendor', 'admin']
    if role not in valid_roles:
        return jsonify({
            'error' : f'Invalid role. user role must be: {",".join(valid_roles)}'
        }), 400
    
    #evaluate password strength

    if len(password) < 8:
        return jsonify ({
            'error': 'password must be atleast 8 charectors long'
        }), 400
    
    #creating user
    try:
        user = user_model.create_user(email, password, name, role)
    except Exception as e:
        logger.error(f"Error creating user: {email}, {str(e)}")
        return jsonify({'error': 'internal server error'}), 500
    if user:
        logger.info(f"REGISTRATION COMPLETE: {email}")
        return jsonify({
            'message': 'registration succesful',
            'user': {
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
            }
        }), 201
    else:
        return jsonify({'error': 'Email already exists'}), 409
    

'''adding login routes'''
@bp.route('/login', methods = ['GET'])
def login_page():
    ''' display login page'''

    return render_template('auth/login.html')
    
@bp.route('/login', methods = ['POST'])
def login():
    '''authenticates user and creates session
    gets email and password from request
    password verified using usermodel
    returns success response'''

    data = request.get_json() or request.form.to_dict()

    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    #validating inputs

    if not email or not password:
        return jsonify({"error": 'email and passwrod required'}), 400
        
    #verifying credentials

    user = user_model.verify_password(email,password)

    if user:
        session['user_email'] = user ['email']
        session['user_name'] = user ['name']
        session['user_role'] = user ['role']
        session.permanent = True # creates session storing it using cookies

        logger.info(f"user logged in: {email}")

        return jsonify({
            'message': 'login successful',
            'user':{
                'email': user['email'],
                'name': user ['name'],
                'role': user ['role'],
            }
         }), 200
    else:
        logger.warning(f"failed to login: {email}")
        return jsonify({'error': 'invalid email address or password'}), 401
        

'''creating log out route'''
@bp.route('logout', methods = ['POST', 'GET'])
def logout():
    '''logs out user and clears session
    clears all session data and redirects to homepage'''

    email = session.get('user_email')
    session.clear()
    logger.info(f"user logged out: {email}")
    return redirect(url_for('index')) 
    # redirects to home page and removes all session data

    '''adding profile routes'''

@bp.route('/profile', methods=['GET'])
@required_login # user must be logged in
def profile():
    '''gets current pofile information requires the user must be logged in '''
    user = user_model.get_user_by_email(session['user_email'])
    if user:
        user_data = user.copy()
        user_data.pop('password_hash', None)
        return jsonify(user_data), 200
    return jsonify({'error': 'user not found'}), 404

@bp.route('/profile', methods = ['PUT'])
@required_login

def update_profile():
    '''updates current user profile'''

    data = request.get_json()
    
    #only allowed certied fields to be setup

    allowed_fields = ['name', 'phone', 'address']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return jsonify ({'error: no valid fields to update'}), 400
    # updating user
    try:
        user = user_model.get_user_by_email(session['user_email'])

        if not user:
            return jsonify({'error': 'user not found'}), 404

        if 'name' in update_data:
            session['user_name'] = update_data['name']

        user_model.update_user(session['user_email'], update_data)
        return jsonify({'message' : 'profile updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating profile for {session['user_email']}: {str(e)}")
        return jsonify({'error': 'internal server error'}), 500 
    
    Json

    
