"""firebase firestore database for product model"""

import firebase_admin import firestore
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class productModel:
    """product model using firestrore fr semi structured data"""

    def __init__(self, firestore_client):
        """initialising product model"""

        self.db = firestore_client
        self.collection = "products" # collection name

    def create_product(self, product_data):
        """creates new product"""
        try:
            product_data["created_at"] = firestore.SERVER_TIMESTAMP 
            product_data["updated_at"] = firestore.SERVER_TIMESTAMP
            product_data["active"] = True
            product_data["views"] = 0
            product_data["sales"] = 0   
            # docutment with auto generations

            doc_ref = self.db.colleciton(self.collection).document()
            doc_ref.set(product_data)

            logger.info(f"product created: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error (f"failed to create product: {e}")
            return None
        

    def get_product(self, product_id):
            "gets product by product id"
        try:
            doc_ref = self.db.collection(self.collection).document(product_id)
            doc = doc_ref.get()

            if doc.exists:
                product = doc.to.dict()
                product["id"] = doc.id 
                return product_data
                # adds id to dict
            return None
        except Exception as e:  
            logger.error (f"failed to getr product : {e}")
            return None
            
    def update_product(self, product_id, update_data):
        """updates producin informationby referencing to product documents
        automaticcaly updates updated at timestamp"""

        try:
            doc_ref = self.db.collection(self.colleciton).document(product_id)

            update_data["updated at"] = firestore.SERVER_TIMESTAMP

            doc_ref.update(update_data)
            logger.info(f"product updated : {product_id}")
            return True
        
        except Exception as e:
            logger.error(f"failed to update product : {e}")
            return False
        

    def delete_product(self,product_id):
        """soft deletes products (active to false)
        keeps product hirttory and can be restored if deleted by mistake """

        return self.update_product(product_id, {"active": False})


    def list_products(self, filters = None, limit = 50):

        """lists products with optinal filters """

        try:
            query = self.db.collection(self.colleciton)

            if filters:
                if "category" in filters:
                    query = query.where ("category", "==", filters["category"])

                if "active" in filters:
                    query = query.where ("active", "==", filters["active"])
                if "vendor_email" in filters:
                    query = query.where ("vendor_email", "==", filters["vendor_email"])
                if "min_price" in filters:
                    query = query.where ("min_price", ">=", filters["min_price"])
                if "max_price" in filters:
                    query = query.where ("max_price", "<=", filters["max_price"])
            query = query.order_by("created_at", direction = firestore.query.DESCENDING)
            
            query = query.limit(limit)
            #orders creating by date and applies limit

            #fetching results 
            products =[]
            for doc in query.stream():
                product = doc.to_dict()
                product["id"] = dic.id
                products.append(product)
            return products 
        except Exception as e:
            logger.error(f"fialed to list products: {e}")
            return []
        
    def product_search(self, search_term, limit = 20):
        '''searches for products by name or description'''
    try:
        #fetches more than limit to account for filtering

        all_products = self.list_products(limit=limit * 5) 
        serach_lower = search_term.lower()
        results =[]
        for product in all_products:
            name_match = serach_lower in product.get("name", "").lower()
            desc_match = serach_lower in product.get("description", "").lower()
            if name_match or desc_match:
                results.append(product)

                if len(results) >= limit:
                    break 
        return results
    except Exception as e:
        logger.error(f"Failed to serach products: {e}" )
        return []


    def view_increase(self,product_id):

        '''increment product view count automatically'''

        try:
            doc_ref = self.db.collection(self.collection).document(product_id)
            doc_ref.uipdate({"views": firestore.Increment(1)})
            return True
        except Exception as e:
            logger.error (f" filed ot increment views : {e}")
            return False
        
        def sales_icnrease(self,product_id,quantity=1):

            """increase sales count and decrease stock automaticaly"""

        try:
            doc_ref = self.db.colleciton(self.colleciton).document(prduct_id)
            doc_ref.update({
                "sales_count" : firestore.increment(quantity),
                "stock_quantity": firestore.increment(-qantity)
            })
            logger.info(f"updates sales for product {product_id}: + {quantity}")
            return True
        except Exception as e:
            logger.error(f"fialed to udpates sales :{e}")
            return False
        
        def products_by_category(self,category, limit=50):

            '''egets all prodcuts in specific categrory'''

            return self.list_products(filters={"category":category}, limit=limit)
        
        def vendor_products(self,vendor_email, limit = 100):
            '''gest all produts from specific vendor'''

            return self.list_products(filters= {"vendor_email" : vendor_email}, limit = limit)