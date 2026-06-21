from datetime import datetime
from decimal import Decimal

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.offers.services import OfferService
from app.transactions.models import Transaction
from app import db
from app.services.notification_service import NotificationService
from app.listings.models import Item
from app.offers.forms import  makeOfferForm, rejectOfferForm, validateOfferForm
from app.offers.models import Offer
from app.auth.models import Notification
from sqlalchemy import desc,or_
from app.offers import bp


@bp.route('/')
@login_required
def index():
    """mark as read notification"""
    NotificationService.mark_as_read_by_type(current_user.id,"offer")
    """Main offers page with both received and sent offers"""
    company = current_user.owned_company
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')  # all, received, sent
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build received offers query (offers made to this company's listings)
    received_query = Offer.query.join(Item).filter(
        Item.company_id == company.id
    )
    
    # Build sent offers query (offers made by this company)
    sent_query = Offer.query.filter(
        Offer.sender_company_id == company.id
    )
    
    # Apply status filters
    if status_filter != 'all':
        received_query = received_query.filter(Offer.status == status_filter)
        sent_query = sent_query.filter(Offer.status == status_filter)
    
    # Get counts for badges
    received_counts = {
        'total': Offer.query.join(Item).filter(Item.company_id == company.id).count(),
        'pending': Offer.query.join(Item).filter(
            Item.company_id == company.id,
            Offer.status == 'pending'
        ).count(),
        'accepted': Offer.query.join(Item).filter(
            Item.company_id == company.id,
            Offer.status == 'accepted'
        ).count(),
        'rejected': Offer.query.join(Item).filter(
            Item.company_id == company.id,
            Offer.status == 'rejected'
        ).count(),
        'expired': Offer.query.join(Item).filter(
            Item.company_id == company.id,
            Offer.status == 'expired'
        ).count(),
        'countered': Offer.query.join(Item).filter(
            Item.company_id == company.id,
            Offer.status == 'countered'
        ).count()
    }
    
    sent_counts = {
        'total': Offer.query.filter(Offer.sender_company_id == company.id).count(),
        'pending': Offer.query.filter(
            Offer.sender_company_id == company.id,
            Offer.status == 'pending'
        ).count(),
        'accepted': Offer.query.filter(
            Offer.sender_company_id == company.id,
            Offer.status == 'accepted'
        ).count(),
        'rejected': Offer.query.filter(
            Offer.sender_company_id == company.id,
            Offer.status == 'rejected'
        ).count(),
        'expired': Offer.query.filter(
            Offer.sender_company_id == company.id,
            Offer.status == 'expired'
        ).count(),
        'countered': Offer.query.filter(
            Offer.sender_company_id == company.id,
            Offer.status == 'countered'
        ).count()
    }
    
    # Order by most recent
    received_query = received_query.order_by(desc(Offer.created_at))
    sent_query = sent_query.order_by(desc(Offer.created_at))
    
    # Paginate
    if type_filter == 'received':
        pagination = received_query.paginate(page=page, per_page=per_page, error_out=False)
        offers = pagination.items
        current_type = 'received'
    elif type_filter == 'sent':
        pagination = sent_query.paginate(page=page, per_page=per_page, error_out=False)
        offers = pagination.items
        current_type = 'sent'
    else:
        # Combine both for 'all' view (more complex, using union)
        # For simplicity, we'll show received first then sent, or use separate queries
        received_pagination = received_query.paginate(page=page, per_page=per_page//2, error_out=False)
        sent_pagination = sent_query.paginate(page=page, per_page=per_page//2, error_out=False)
        offers = received_pagination.items + sent_pagination.items
        offers.sort(key=lambda x: x.created_at, reverse=True)
        pagination = None
        current_type = 'all'
    
    # Get offer statistics
    total_offers = received_counts['total'] + sent_counts['total']
    pending_total = received_counts['pending'] + sent_counts['pending']
    accepted_total = received_counts['accepted'] + sent_counts['accepted']
    
    # Calculate average response time
    responded_offers = Offer.query.join(Item).filter(
        Item.company_id == company.id,
        Offer.responded_at.isnot(None)
    ).limit(100).all()
    
    if responded_offers:
        avg_response = sum(
            (offer.responded_at - offer.created_at).total_seconds() / 3600
            for offer in responded_offers
        ) / len(responded_offers)
        avg_response_hours = round(avg_response, 1)
    else:
        avg_response_hours = 0
    
    return render_template('offers_index.html',
                         offers=offers,
                         pagination=pagination,
                         received_counts=received_counts,
                         sent_counts=sent_counts,
                         total_offers=total_offers,
                         pending_total=pending_total,
                         accepted_total=accepted_total,
                         avg_response_hours=avg_response_hours,
                         current_status=status_filter,
                         current_type=current_type,now=datetime.now())

@bp.route('/create/<int:listing_id>',methods=['POST','GET'])
@login_required
def create_offer(listing_id):
    """Create a new offer for a listing"""
    
    # Get the listing
    listing = Item.query.get_or_404(listing_id)
    
    # Check if listing is available for offers
    if listing.status != 'active':
        flash('This listing is no longer available for offers.', 'danger')
        return redirect(url_for('listings.detail', listing_id=listing.id))
    
    if listing.expires_at and datetime.utcnow() > listing.expires_at:
        flash('This listing has expired.', 'danger')
        return redirect(url_for('listings.detail', listing_id=listing.id))
    
    # Check if user is trying to offer on their own listing
    if listing.company_id == current_user.company_id:
        flash('You cannot make an offer on your own listing.', 'warning')
        return redirect(url_for('listings.detail', listing_id=listing.id))
    
    # Check if user already has a pending offer
    existing_offer = Offer.query.filter(
        Offer.item_id == listing.id,
        Offer.sender_company_id == current_user.company_id,
        Offer.status == 'pending'
    ).first()
    
    if existing_offer:
        flash('You already have a pending offer on this listing.', 'info')
        return redirect(url_for('offers.index'))
    
    # Initialize form
    form = makeOfferForm()
    
    if form.validate_on_submit():
        
        print("----------------offer")
        try:
            # Create the offer
            offer = OfferService.create_offer(
                listing=listing,
                sender_company=current_user.owned_company,
                receiver_company=listing.owned_company,
                user=current_user,
                price=form.price.data,
                quantity=form.quantity.data,
                message=form.message.data,
                requires_delivery=form.requires_delivery.data,
                delivery_address=form.delivery_address.data
            )
            
            flash(f'Your offer of ${form.price.data:.2f} has been sent to the seller!', 'success')
            
            # Redirect based on user preference
            if request.args.get('redirect') == 'listing':
                return redirect(url_for('listings.detail', listing_id=listing.id))
            else:
                return redirect(url_for('offers.index'))
                
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('An error occurred while creating your offer. Please try again.', 'danger')
            current_app.logger.error(f'Offer creation error: {str(e)}')
    
    # Pre-fill quantity if not specified
    if request.method == 'GET' and not form.quantity.data:
        form.quantity.data = listing.quantity
    
    return render_template(
        'create_offer.html',
        form=form,
        listing=listing
    )



@bp.route('/api/check-offer/<int:listing_id>')
@login_required
def check_offer_status(listing_id):
    """API endpoint to check if user has a pending offer"""
    listing = Item.query.get_or_404(listing_id)
    
    if listing.company_id == current_user.company_id:
        return jsonify({
            'has_offer': False,
            'message': 'This is your listing'
        })
    
    existing_offer = Offer.query.filter(
        Offer.listing_id == listing.id,
        Offer.company_id == current_user.company_id,
        Offer.status == 'pending'
    ).first()
    
    return jsonify({
        'has_offer': existing_offer is not None,
        'offer_id': existing_offer.id if existing_offer else None,
        'message': 'You already have a pending offer' if existing_offer else None
    })

@bp.route('/api/validate-offer', methods=['POST'])
@login_required
def validate_offer():
    """API endpoint for real-time offer validation"""
    data = request.json
    listing_id = data.get('listing_id')
    price = data.get('price')
    quantity = data.get('quantity')
    
    listing = Item.query.get(listing_id)
    if not listing:
        return jsonify({'valid': False, 'error': 'Item not found'})
    
    errors = {}
    
    # Validate price
    try:
        price_val = float(price)
        if price_val <= 0:
            errors['price'] = 'Price must be greater than 0'
        elif listing.price and price_val > listing.price * 2:
            errors['price'] = f'Price seems high. Maximum suggested: ${listing.price * 2:.2f}'
        elif listing.price and price_val < listing.price * 0.1:
            errors['price'] = f'Price seems low. Minimum suggested: ${listing.price * 0.1:.2f}'
    except (TypeError, ValueError):
        errors['price'] = 'Invalid price format'
    
    # Validate quantity
    if quantity:
        try:
            quantity_val = float(quantity)
            if quantity_val <= 0:
                errors['quantity'] = 'Quantity must be greater than 0'
            elif quantity_val > listing.quantity:
                errors['quantity'] = f'Quantity cannot exceed {listing.quantity} {listing.unit}'
        except (TypeError, ValueError):
            errors['quantity'] = 'Invalid quantity format'
    
    # Check for duplicate offer
    existing_offer = Offer.query.filter(
        Offer.listing_id == listing.id,
        Offer.company_id == current_user.company_id,
        Offer.status == 'pending'
    ).first()
    
    if existing_offer:
        errors['general'] = 'You already have a pending offer on this listing'
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors
    })


@bp.route('/<int:offer_id>/accept', methods=['POST','GET'])
@login_required
def accept_offer(offer_id):
    """Accept an offer"""
    offer = Offer.query.get_or_404(offer_id)
    listing = offer.item
    commission_rate=current_user.owned_company.commission_rate
    
    
    # Check if user can accept this offer (must be seller of the listing)
    if listing.company_id != current_user.company_id:
        flash('You do not have permission to accept this offer.', 'danger')
        return redirect(url_for('offers.index'))
    
    if offer.status != 'pending':
        flash('This offer is no longer available.', 'warning')
        return redirect(url_for('offers.offers_index'))
    
    # Accept the offer
    offer.status="accepted"
    offer.accepted_at=datetime.now()
    # Create transaction
    
    total_amount=float(offer.offered_price*offer.quantity_requested)
    commission_amount=Decimal(total_amount)*commission_rate
    seller_net_amount=Decimal(total_amount)-commission_amount
   
    transaction = Transaction(
        item_id=listing.id,
        offer_id=offer.id,
        seller_company_id=offer.seller_company_id,
        buyer_company_id=offer.buyer_company_id,
        seller_manager_id=offer.seller_id,
        buyer_manager_id=offer.buyer_id,
        price=offer.offered_price,
        total_amount=total_amount,
        commission_rate=commission_rate,
        commission_amount=commission_amount,
        seller_net_amount=seller_net_amount,
        quantity=offer.quantity_requested ,
        status='pending',
        payment_status='pending'
    )
    
    db.session.add(transaction)

    #update quantity
    offer.item.available_quantity-=offer.quantity_requested
    offer.item.solde_quantity+=offer.quantity_requested
    if offer.item.solde_quantity==offer.item.quantity:
         offer.item.status="solde" 
    db.session.commit()
    
    # Create notification for buyer
    notification = Notification(
        user_id=offer.buyer_id,
        type='offer_accepted',
        title='Your offer was accepted!',
        message=f'Your offer of ${offer.offered_price} for "{listing.name}" has been accepted.',
    
    )
    db.session.add(notification)
    
    db.session.commit()
    
    flash(f'Offer accepted! Transaction #{transaction.id} has been created.', 'success')
    return redirect(url_for('transactions.detail', transaction_id=transaction.id))

@bp.route('/<int:offer_id>/reject', methods=['POST'])
@login_required
def reject_offer(offer_id):
    """Reject an offer"""
    offer = Offer.query.get_or_404(offer_id)
    listing = offer.item
    
    if listing.company_id != current_user.company_id:
        flash('You do not have permission to reject this offer.', 'danger')
        return redirect(url_for('offers.index'))
    
    if offer.status != 'pending':
        flash('This offer is no longer available.', 'warning')
        return redirect(url_for('offers.index'))
    
    offer.status="rejected"
    user_id=0
    if offer.is_counter:
        user_id=offer.seller_id
    else:
        user_id=offer.buyer_id
    # Create notification
    notification = Notification(
        user_id=user_id,
        type='offer_rejected',
        title='Your offer was declined',
        message=f'Your offer of ${offer.offered_price} for "{listing.name}" was declined.',
        #related_type='offer',
        #related_id=offer.id
    )
    db.session.add(notification)
    db.session.commit()
    
    flash('Offer rejected.', 'info')
    return redirect(url_for('offers.index'))

@bp.route('/<int:offer_id>/counter', methods=['GET', 'POST'])
@login_required
def counter_offer(offer_id):
    """Counter an offer"""
    original_offer = Offer.query.get_or_404(offer_id)
    listing = original_offer.listing
    
    # Check permissions
    if listing.company_id != current_user.company_id:
        flash('You do not have permission to counter this offer.', 'danger')
        return redirect(url_for('offers.index'))
    
    if original_offer.status != 'pending':
        flash('This offer is no longer available.', 'warning')
        return redirect(url_for('offers.index'))
    
    form = makeOfferForm()
    
    if form.validate_on_submit():
        # Create counter offer
        counter = Offer(
            listing_id=listing.id,
            company_id=original_offer.company_id,
            created_by_id=original_offer.created_by_id,
            price=form.price.data,
            quantity=form.quantity.data,
            message=form.message.data,
            parent_offer_id=original_offer.id,
            status='pending'
        )
        
        db.session.add(counter)
        
        # Mark original as countered
        original_offer.status = 'countered'
        original_offer.responded_at = datetime.utcnow()
        
        # Create notification
        notification = Notification(
            user_id=original_offer.created_by_id,
            type='offer_countered',
            title='Counter offer received',
            message=f'The seller has countered your offer with ${form.price.data}.',
            related_type='offer',
            related_id=counter.id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        flash('Counter offer sent!', 'success')
        return redirect(url_for('offers.index'))
    
    # Pre-fill form with original offer details
    form.price.data = original_offer.price
    form.quantity.data = original_offer.quantity
    
    return render_template('offers/counter_offer.html', 
                         form=form, 
                         original_offer=original_offer,
                         listing=listing)

@bp.route('/<int:offer_id>/cancel', methods=['POST'])
@login_required
def cancel_offer(offer_id):
    """Withdraw an offer (only by sender)"""
    offer = Offer.query.get_or_404(offer_id)
    
    if offer.sender_company_id != current_user.company_id:
        flash('You can only withdraw your own offers.', 'danger')
        return redirect(url_for('offers.index'))
    
    if offer.status != 'pending':
        flash('This offer cannot be withdrawn.', 'warning')
        return redirect(url_for('offers.index'))
    
    offer.cancel()
    
    flash('Offer withdrawn successfully.', 'info')
    return redirect(url_for('offers.index'))

@bp.route('/api/offers/stats')
@login_required
def offer_stats():
    """API endpoint for offer statistics"""
    company = current_user.company
    
    # Get weekly offer activity
    today = datetime.utcnow().date()
    weekly_stats = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        
        received = Offer.query.join(Item).filter(
            Item.company_id == company.id,
            func.date(Offer.created_at) == date
        ).count()
        
        sent = Offer.query.filter(
            Offer.company_id == company.id,
            func.date(Offer.created_at) == date
        ).count()
        
        weekly_stats.append({
            'date': date.strftime('%a'),
            'received': received,
            'sent': sent
        })
    
    return jsonify({
        'success': True,
        'data': weekly_stats
    })
    