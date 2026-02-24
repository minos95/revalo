from revelo_package import db,bcrypt

class Company(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    items = db.relationship('Item', back_populates='owned_company',lazy=True)
    users = db.relationship('User', back_populates='owned_company',lazy=True)
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

class User(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    full_name = db.Column(db.String(length=30),nullable=False)
    phone = db.Column(db.String(length=30),nullable=False)
    email = db.Column(db.String(length=50),nullable=False)
    password_hash=db.Column(db.String(length=50),nullable=False)
    role = db.Column(db.String(length=30),nullable=False)  # owner, manager, employee
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    owned_company = db.relationship("Company", back_populates="users")

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
    offered_price = db.Column(db.Integer(),nullable=False)
    quantity_requested = db.Column(db.Integer(),nullable=False)
    message = db.Column(db.String(length=300),nullable=False)
    status = db.Column(db.String(length=30),nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())


class Transaction(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    offer_id = db.Column(db.Integer(),db.ForeignKey('offer.id'))
    buyer_company_id = db.Column(db.Integer(),nullable=False)
    seller_company_id = db.Column(db.Integer(),nullable=False)
    quantity = db.Column(db.Integer(),nullable=False)
    payement_status = db.Column(db.String(length=30),nullable=False)
    dilivery_status = db.Column(db.String(length=30),nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Category(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(length=30),nullable=False)
    Description=db.Column(db.String(length=300),nullable=False)
    items=db.relationship("Item", back_populates="owned_category",lazy=True)
   

class Item(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    company_id= db.Column(db.Integer(),db.ForeignKey('company.id'))
    category_id= db.Column(db.Integer(),db.ForeignKey('category.id'))
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
    owned_company = db.relationship("Company", back_populates="items")
    owned_category=db.relationship("Category",back_populates="items")
    def __repr__(self):
        return f'Item {self.name}'

class Image(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    item_id= db.Column(db.Integer(),db.ForeignKey('item.id'))
    uri=db.Column(db.String(length=30),nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

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
    
    

