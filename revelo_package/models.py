from revelo_package import db,bcrypt,login_manager
from flask_login import UserMixin



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
class Company(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    items = db.relationship('Item', back_populates='owned_company',lazy=True)
    users = db.relationship('User', back_populates='owned_company',lazy=True)
    buy_transactions=db.relationship('Transaction', back_populates='buyer_company',foreign_keys="Transaction.buyer_company_id",lazy=True)
    sell_transactions=db.relationship('Transaction', back_populates='seller_company',foreign_keys="Transaction.seller_company_id",lazy=True)
    name = db.Column(db.String(length=30),nullable=False,unique=True)
    address = db.Column(db.String(length=30),nullable=False)
    country = db.Column(db.String(length=30),nullable=False)
    city = db.Column(db.String(length=30),nullable=False)
    company_type = db.Column(db.String(length=30),nullable=False) #generator, recycler, trader
    activity = db.Column(db.String(length=30),nullable=False)
    rc = db.Column(db.String(length=30))
    nif = db.Column(db.String(length=30))
    nis = db.Column(db.String(length=30))
    referal = db.Column(db.String(length=30))
    verified=db.Column(db.Boolean())
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer(),primary_key=True)
    company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    full_name = db.Column(db.String(length=30),nullable=False)
    phone = db.Column(db.String(length=30),nullable=False)
    email = db.Column(db.String(length=50),nullable=False)
    email_verified=db.Column(db.Boolean())
    password_hash=db.Column(db.String(length=50),nullable=False)
    role = db.Column(db.String(length=30),nullable=False)  # owner, manager, employee
    authorized=db.Column(db.Boolean())
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    owned_company = db.relationship("Company", back_populates="users")
    items = db.relationship('Item', back_populates='owned_user',lazy=True)
    @property
    def password(self):
        return self.password
    
    @password.setter
    def password(self,plain_text_password):
        self.password_hash=bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    def check_password_correction(self,attempted_password):
        return bcrypt.check_password_hash(self.password_hash,attempted_password)

class Offer(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    item_id = db.Column(db.Integer(),db.ForeignKey('item.id'))
    buyer_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    seller_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    buyer_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    seller_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    offered_price = db.Column(db.Integer(),nullable=False)
    quantity_requested = db.Column(db.Integer(),nullable=False)
    unit = db.Column(db.String(length=300),nullable=False)
    message = db.Column(db.String(length=300))
    status = db.Column(db.String(length=30),default="pending")#pending/countred/accepted/rejected/cancelled/expired
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    accepted_at=db.Column(db.DateTime(timezone=True))
    owned_offer = db.relationship("Item", back_populates="offers")

class Transaction(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    offer_id = db.Column(db.Integer(),db.ForeignKey('offer.id'))
    item_id = db.Column(db.Integer(),db.ForeignKey('item.id'))
    buyer_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    seller_company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    price = db.Column(db.Integer(),nullable=False)
    quantity = db.Column(db.Integer(),nullable=False)
    unit = db.Column(db.String(),nullable=False)
    payement_status = db.Column(db.String(length=30),nullable=False,default="pending") #pending/confirmed/in_progress/completed/disputed
    dilivery_status = db.Column(db.String(length=30),nullable=False,default="pending")
    total_amount=db.Column(db.Integer(),nullable=False)
    commission_rate=db.Column(db.Integer(),nullable=False)
    commission_amount=db.Column(db.Integer(),nullable=False)
    seller_net_amount=db.Column(db.Integer(),nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    transactions = db.relationship("Review", back_populates="owned_review",lazy=True)
    owned_transaction = db.relationship("Item", back_populates="transactions",lazy=True)
    buyer_company = db.relationship('Company', back_populates='buy_transactions',foreign_keys=[buyer_company_id],lazy=True)
    seller_company = db.relationship('Company', back_populates='sell_transactions',foreign_keys=[seller_company_id],lazy=True)
class Category(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(length=30),nullable=False)
    Description=db.Column(db.String(length=300),nullable=False)
    items=db.relationship("Item", back_populates="owned_category",lazy=True)

    qualities = db.relationship('Quality_attributes', back_populates='owned_quality',lazy=True)
   

class Item(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    company_id= db.Column(db.Integer(),db.ForeignKey('company.id'))
    category_id= db.Column(db.Integer(),db.ForeignKey('category.id'))
    user_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    name=db.Column(db.String(length=30),nullable=False)
    description=db.Column(db.String(length=1024))
    unit= db.Column(db.String(length=30),nullable=False)
    quantity= db.Column(db.Integer(),nullable=False) 
    location=db.Column(db.String(length=30))
    sell_type=db.Column(db.String(length=30))
    price=db.Column(db.Integer(),nullable=False) 
    status=db.Column(db.String(length=30),default="open") #open/closed/sold
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    images=db.relationship('Image',backref='owned_item',lazy=True)
    offers=db.relationship('Offer',backref='owned_item',lazy=True)
    views=db.relationship('View',backref='owned_item',lazy=True)
    owned_user = db.relationship("User", back_populates="items")
    owned_company = db.relationship("Company", back_populates="items")
    owned_category=db.relationship("Category",back_populates="items")
    offers = db.relationship('Offer', back_populates='owned_offer',lazy=True)
    transactions = db.relationship('Transaction', back_populates='owned_transaction',lazy=True)
    images = db.relationship('Image', back_populates='owned_image',lazy=True)
    qualities = db.relationship('Item_quality_values', back_populates='owned_item',lazy=True)
    def __repr__(self):
        return f'Item {self.name}'

class Image(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    item_id= db.Column(db.Integer(),db.ForeignKey('item.id'))
    default=db.Column(db.Boolean(),default=False)
    uri=db.Column(db.String(length=30),nullable="False")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    owned_image = db.relationship('Item', back_populates='images',lazy=True)
    

class View(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    company_id= db.Column(db.Integer(),db.ForeignKey('company.id'))
    item_id=db.Column(db.Integer(),db.ForeignKey('item.id'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Review(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    transaction_id= db.Column(db.Integer(),db.ForeignKey('transaction.id'))
    reviewer_company_id = db.Column(db.Integer(),nullable=False)
    reviewed_company_id = db.Column(db.Integer(),nullable=False)
    comment = db.Column(db.String(length=300),nullable=False)
    rating = db.Column(db.Integer(),nullable=False) #1-5
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    owned_review = db.relationship("Transaction", back_populates="transactions",lazy=True)
    
    
class Quality_attributes(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    category_id= db.Column(db.Integer(),db.ForeignKey('category.id'))
    name=db.Column(db.String(length=30),nullable=False) #--- cleanliness, Compressed, Rust level, Crushed
    field=db.Column(db.String(length=30),nullable=False) #-----select,boolean,number,text
    unit=db.Column(db.String(length=30))
    is_required=db.Column(db.Boolean())
    owned_quality = db.relationship('Category', back_populates='qualities',lazy=True)
    options=db.relationship('Quality_attribute_options', back_populates='owned_attribute_options',lazy=True)

class Quality_attribute_options(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    attribute_id= db.Column(db.Integer(),db.ForeignKey('quality_attributes.id'))
    value=db.Column(db.String(length=30),nullable=False) #----cleanliness: clean ,mixed dirty, rust level: low,medium,high
    owned_attribute_options=db.relationship('Quality_attributes', back_populates='options',lazy=True)
class Item_quality_values(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    item_id= db.Column(db.Integer(),db.ForeignKey('item.id'))
    attribute_id= db.Column(db.Integer(),db.ForeignKey('quality_attributes.id'))
    option_id=db.Column(db.Integer(),db.ForeignKey('quality_attribute_options.id'))
    value_text=db.Column(db.String(length=30))
    value_number=db.Column(db.Integer())
    owned_item = db.relationship('Item', back_populates='qualities',lazy=True)