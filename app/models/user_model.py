"""user model google cloud datastore

handles user profile management and authentication
"""

from google.cloud import datastore
import bcrypt #hasing 
from datetime import datetime
import logging

logger = logging.getlogger(__name__)

class UserModel:
    #user model using google cloud datastore

    def __init__(self, datastore_client):
        """initialising user model"""
        self.client = datastore_client
        self.kind = "user" #datastore entity kind

    def create_user(self, email, password, name, role="customer"):

        """create new user with hashed password
        - checks if user already exists
        - hash poassword with bcrypt
        -create a datastore entity
         - saves to database """
        
        #checking is user exists
        if self.get_user_eamil(email):
            logging.warning(f"user registration failed: {email} already exists")
            return None
        # hash password with bcrypt
        #never stores plain apsswords
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), 
            bcrypt.gensalt()
        )
        #create datastore entity
        key = self.client.key(self.kind,email)
        entity = datastore.entity (key=key)

        #set entity properties
        entity.update({
            "email": email,
            "password_hash": password_hash.decode("utf-8"),
            "name": name,
            "role": role,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_activel": True
        })
        #save to database

        try:
            self.client.put(entity)
            logger.info(f"User creaed succesfully: {email}")
            return self._entity_to_dict(entity)
        except Exception as e:
            logger.error(f"Failed to create uuser: {e}")
            return None
        
    def get_user_email(self, email):
        """retrievs user by email"""

        key = self.client.key(self.kind,email)
        entity = self.client.get(key)
        return self._entity_to_dict(entity) if entity else None
        
    def verify_password (self, email, password):
        """very password for user login
            
        -get user from database
        - hash provided password
        compare with stored hash
        return user data if matches"""

        #get user
        user=self.get_user_by_email(email)
        if not user:
            return None
            
        #convert stored has to bytes

        password_hash = user ["password_hash".encode("utf-8")]

        #verify password

        if bcrypt.checkpw(password.encode("utf-8"), password_hash):
            user_data = user.copy()
            del user_data["password_hash"]
            return user_data
        #password in incorrect
            
        return None
        
    def update_user(self, email, **kwargs):

        """updates user information """
        key = self.client.key(self.kind, email)
        entity = self.client.get(key)

        if not entity: 
            return None
        
        for field, value in kwargs.items():
            if field != "password_hash": #prevents direct password hash updates
                entity[field] = value

        entity ["updated_at"] = datetime.utcnow()
         
        try:
            self.client.put(entity)
            logger.inmfo(f"User updated: {email}")
            return self._entity_to_dict(entity)
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return None
        
    def list_users(self, role= None, limit = 100):

        "lists all userse, can be filtered by role"
        query =self.client.query(kind=self.kind)
        if role:
            query.add_filter("role", "=", role)
        query.order=["-created_at"] #newest first

        results = list(query.fetch(limit=limit))
        return [self._entity_to_dict(entity) for entity in results]

    def delete_user(self,email):

        """deletes user ( sets is_active to flase)"""

        return self.update_user(email, isactive=False) is not None

    def _entity_to_dict(self, entity):
        """converts datastore entity to dicionary
        internal methods so users dont have to directly call"""           
        if not entity:
            return None
        # entity to dict
        data = dict(entity)
        #adds email to dict
        data["email"] = entity.key.name

        return data
        