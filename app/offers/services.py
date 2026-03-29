

from app import db

from datetime import datetime, timedelta
from flask import current_app

from app.auth.models import Notification
from app.offers.models import Offer


class OfferService:
    """Service class for offer operations"""
    
    @staticmethod
    def create_offer(listing, sender_company,receiver_company, user, price, quantity=None, message=None, requires_delivery=False, delivery_address=None):
        """Create a new offer with validation"""
        
        # Check if listing is active
        if listing.status != 'active':
            raise ValueError('This listing is no longer active')
        
        # Check if listing is expired
        if listing.expires_at and datetime.utcnow() > listing.expires_at:
            raise ValueError('This listing has expired')
        
        # Check if user already has a pending offer
        existing_offer = Offer.query.filter(
            Offer.item_id == listing.id,
            Offer.sender_company_id == sender_company.id,
            Offer.status == 'pending'
        ).first()
        
        if existing_offer:
            raise ValueError('You already have a pending offer on this listing')
        
        # Check if user is trying to offer on their own listing
        if listing.company_id == user.owned_company.id:
            raise ValueError('You cannot make an offer on your own listing')
        
        # Validate quantity
        if quantity and quantity > listing.quantity:
            raise ValueError(f'Quantity cannot exceed available {listing.quantity} {listing.unit}')
        
        # Set default quantity if not specified
        if not quantity:
            quantity = listing.quantity
        
        # Create offer
        offer = Offer(
            item_id=listing.id,
            sender_company_id=sender_company.id,
            buyer_company_id=sender_company.id,
            seller_company_id=receiver_company.id,
            buyer_id=user.id,
            seller_id=listing.user_id,
            offered_price=price,
            quantity_requested=quantity,
            unit=listing.unit,
            message=message,
            status='pending',
            expires_at=datetime.utcnow() + timedelta(days=10),
            requires_delivery=requires_delivery,
            delivery_address=delivery_address
        )
        
        db.session.add(offer)
        db.session.flush()
        
        # Create notification for seller
        notification = Notification(
            user_id=listing.user_id,
            type='offer_received',
            title='New Offer Received',
            message=f'{sender_company.name} has made an offer of ${price:.2f} on your listing "{listing.name}"',
          
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return offer
    
    @staticmethod
    def check_duplicate_offer(listing_id, company_id):
        """Check if company already has a pending offer"""
        return Offer.query.filter(
            Offer.item_id == listing_id,
            Offer.sender_company_id == company_id,
            Offer.status == 'pending'
        ).first() is not None
    
    @staticmethod
    def get_offer_stats(company_id):
        """Get offer statistics for a company"""
        total_offers = Offer.query.filter_by(company_id=company_id).count()
        pending_offers = Offer.query.filter_by(company_id=company_id, status='pending').count()
        accepted_offers = Offer.query.filter_by(company_id=company_id, status='accepted').count()
        
        return {
            'total': total_offers,
            'pending': pending_offers,
            'accepted': accepted_offers
        }