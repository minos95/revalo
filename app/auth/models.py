from app import db,bcrypt,login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
class Company(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String(length=30),nullable=False,unique=True)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(200))
    
    address = db.Column(db.String(length=30),nullable=False)
    country = db.Column(db.String(length=30),nullable=False)
    city = db.Column(db.String(length=30),nullable=False)
    company_type = db.Column(db.String(length=30),nullable=False) #generator, recycler, trader
    activity = db.Column(db.String(length=30),nullable=False)
    rc = db.Column(db.String(length=30))
    nif = db.Column(db.String(length=30))
    nis = db.Column(db.String(length=30))
    referal = db.Column(db.String(length=30))
    verified=db.Column(db.String(),default="pending")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    items = db.relationship('Item', back_populates='owned_company',lazy=True)
    users = db.relationship('User', back_populates='owned_company',lazy=True)
    buy_transactions=db.relationship('Transaction', back_populates='buyer_company',foreign_keys="Transaction.buyer_company_id",lazy=True)
    sell_transactions=db.relationship('Transaction', back_populates='seller_company',foreign_keys="Transaction.seller_company_id",lazy=True)
    offers = db.relationship("Offer",foreign_keys="Offer.sender_company_id",back_populates="sender_company",lazy=True)
    
class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer(),primary_key=True)
    company_id = db.Column(db.Integer(),db.ForeignKey('company.id'))
    full_name = db.Column(db.String(length=30),nullable=False)
    phone = db.Column(db.String(length=30),nullable=False)
    email = db.Column(db.String(length=50),nullable=False,index=True)
    email_verified=db.Column(db.Boolean(),default=False)
    password_hash=db.Column(db.String(length=50),nullable=False)
    role = db.Column(db.String(length=30),nullable=False)  # owner, manager, employee
    authorized=db.Column(db.Boolean(),default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())


    owned_company = db.relationship("Company", back_populates="users")
    items = db.relationship('Item', back_populates='owned_user',lazy=True)

    transactions_as_seller_manager = db.relationship('Transaction',foreign_keys='Transaction.seller_manager_id', back_populates='seller_manager',lazy=True)
    transactions_as_buyer_manager = db.relationship('Transaction',foreign_keys='Transaction.buyer_manager_id',  back_populates='buyer_manager',lazy=True)

    @property
    def password(self):
        return self.password
    
    @password.setter
    def password(self,plain_text_password):
        self.password_hash=bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    def check_password_correction(self,attempted_password):
        return bcrypt.check_password_hash(self.password_hash,attempted_password)