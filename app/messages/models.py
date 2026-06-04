from datetime import datetime

from app import db
class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Participants
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Link to BOTH (optional)
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id'), nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    
    # Status
    stage = db.Column(db.String(20), default='offer')  # offer, transaction, completed
    is_active = db.Column(db.Boolean, default=True)
    seller_deleted = db.Column(db.Boolean, default=False)
    buyer_deleted = db.Column(db.Boolean, default=False)
    
    # Last message info
    last_message = db.Column(db.Text)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Unread counts
    seller_unread_count = db.Column(db.Integer, default=0)
    buyer_unread_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = db.relationship('User', foreign_keys=[seller_id], backref='seller_conversations')
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='buyer_conversations')
    last_message_sender = db.relationship('User', foreign_keys=[last_message_sender_id])
    transaction = db.relationship('Transaction', backref='conversations')
    item = db.relationship('Item', backref='conversations')
    messages = db.relationship('Message', back_populates='conversation', cascade='all, delete-orphan')
   
    
    def get_other_participant(self, user_id):
        """Get the other participant in the conversation"""
        if self.seller_id == user_id:
            return self.buyer
        return self.seller
    
    def mark_as_read(self, user_id):
        """Mark all messages as read for a user"""
        if self.seller_id == user_id:
            self.seller_unread_count = 0
        else:
            self.buyer_unread_count = 0
        db.session.commit()
    
    def increment_unread(self, user_id):
        """Increment unread count for the other user"""
        if self.seller_id == user_id:
            self.buyer_unread_count += 1
        else:
            self.seller_unread_count += 1
        db.session.commit()


# ============================================
# MESSAGE MODEL
# ============================================
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    
    # Message status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Optional attachments
    has_attachment = db.Column(db.Boolean, default=False)
    attachment_url = db.Column(db.String(500))
    attachment_type = db.Column(db.String(50))  # image, document, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = db.relationship('Conversation', back_populates='messages')
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    def mark_as_read(self):
        """Mark individual message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()