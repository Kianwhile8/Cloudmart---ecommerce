from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import logging


base = declarative_base()
logger= logging.getLogger(__name__)


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    shipping_address = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    items = relationship("OrderItem", back_populates ="order", cascade="all, delete-orphan")

class OrderItem(base):
    '''orders table items'''
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, autoincrement= True)
    product_id = Column(String(100), nullable=False)
    order_id = Column(Integer,ForeignKey('orders.id'), nullable= False)
    product_name = Column(String(255),nullable= False)
    subtotal = Column(float, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(float, nullable= False)

    order = relationship ("order", back_populates="items")

class OrderModel:

    def __init__(self, db_connection_string=None):
        '''initalises database connection'''
        if db_connection_string is None:
            db_connection_string = os.environ.get(
                'DATABSE_URL',
                'mysql+pymysql://root:password@localhost:3306/cloudmart'
            )

        self.engine = create_engine (db_connection_string, echo=False)
        Base.metadata.create_all(self.engine) 
        self.session = sessionmaker(bind=self.engine)
    
    def create_order(self,items, customer_email, payment_method, shipping_address):
        '''creates new order with items'''

        session = self.session()
        try:
            total_amount = sum(item['quantity'] * item ['unit_price'] for item in items)
            order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%D%H%M%S')}"

            #creating order
            order=order(
                order_number=order_number,
                customer_email=customer_email,
                shipping_address=shipping_address,
                payment_method=payment_method,
                total_amount=total_amount,
                status='pending'
            )
            session.add(order)
            session.flush() #gets order ID

            #creaitng order items

            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    unit_price=item['unit_price'],
                    quanitty=item['quanity'],
                    product_name=item['product_naame'],
                    subtotal=item['quantity'] *item['unit_price']
                )
                session.add(order_item)

            session.commit()
            logger.info(F"ORDER CREATED: {order_number}")
            return self._order_to_dict(Order)
        except Exception as e:
            session.rollback()
            logger.error(f"failed to create order: {e}")
            return None
        finally:
            session.close()
    def get_order (self, order_id):
        '''gets order by ID'''
        session=self.session()
        try:
            order = session.query(Order).filter_by(id=order_id).first()
            return self._order_to_dict(order) if order else None
        finally:
            session.close()

    def get_order_by_number(self, order_number):
        '''getting order by order number'''
        session = self.session
        try:
            order = session.query(Order).filter_by(order_number = order_number).first()
            return self._order_to_dict(order) if order else None
        finally:
            session.close()

    def list_all_orders(self, status = None, limit = 100):
        '''lists all orders can be filtered by status'''

        session = self.session()
        try:
            query = session.query(Order)
            if status:
                query = query.filter_by(status=status)
            orders= query.order_by(Order.created_at.desc()).limit(limit).all()
            return [self._order_to_dict(order) for order in orders]
        finally:
            session.close()
        
    def update_order_status(self,order_id, status):
        '''updating order status'''
        session = self.session()
        try:
            order = session.query(Order).filter_by(id=order_id).first()
            if order:
                order.status = status
                order.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Order {order_id} status is now {status}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"failed to update order status: {e}")
            return False
        finally:
            session.close()
    
    def list_customer_orders(self,customer_email, limit=50):
        '''list orders for a customer'''

        session = self.session()
        try:
            orders = session.query(Order)\
                .filter_by(customer_email = customer_email)\
                .order_by(order.created_at.desc())\
                .limit(limit)\
                .all()
            return [self._order_to_dict(orders) for order in orders] 
        finally:
            session.close()
    
    
    def _order_to_dict(self,order):
        '''converts order to diciotnary'''
        
        if not order:
            return None
        
        return{
            'id': order.id,
            'order_number': order.order_number,
            'total_amount': order.total_amount,
            'customer_email': order.customer_email,
            'shipping_address': order.shipping_address,
            'status': order.status,
            'payment_method': order.payment_method,
            'created_at' : order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'items' :[
                {
                    'product_id': item.product_id,
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'subtotal': item.subtotal,
                    'unit price': item.unitprice              
                }
            for item in order.items
            ]
        }

                
                        