from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.services.notification_service import NotificationService
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, and_, desc

from app import db
from app.messages import bp
from app.messages.forms import MessageForm
from app.messages.models import Conversation, Message
from app.auth.models import  User, Notification
from app.transactions.models import Transaction
from app.listings.models import Item as Listing
# ============================================
# INBOX - LIST ALL CONVERSATIONS
# ============================================

@bp.route('/')
@login_required
def index():

    NotificationService.mark_as_read_by_type(current_user.id,"conversation")
    """Show all conversations for the current user"""
    
    # Get all conversations where user is participant
    conversations = Conversation.query.filter(
        or_(
            and_(Conversation.seller_id == current_user.id, Conversation.seller_deleted == False),
            and_(Conversation.buyer_id == current_user.id, Conversation.buyer_deleted == False)
        )
    ).order_by(desc(Conversation.last_message_at)).all()
    
    # Get unread count for badge
    unread_count = 0
    for conv in conversations:
        if conv.seller_id == current_user.id:
            unread_count += conv.seller_unread_count
        else:
            unread_count += conv.buyer_unread_count
    
    return render_template('messages_index.html', 
                         conversations=conversations,
                         unread_count=unread_count)


# ============================================
# CONVERSATION THREAD
# ============================================

@bp.route('/conversation/<int:conversation_id>')
@login_required
def thread(conversation_id):
    """View a specific conversation thread"""
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if user is participant
    if conversation.seller_id != current_user.id and conversation.buyer_id != current_user.id:
        flash('You do not have access to this conversation.', 'danger')
        return redirect(url_for('messages.index'))
    
    # Mark all messages as read for this user
    conversation.mark_as_read(current_user.id)
    
    # Get all messages
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
    
    # Mark individual messages as read
    for message in messages:
        if message.sender_id != current_user.id and not message.is_read:
            message.mark_as_read()
    
    # Get other participant
    other_participant = conversation.get_other_participant(current_user.id)
    
    # Get related transaction/listing info
    transaction = conversation.transaction
    listing = conversation.item
    
    # Message form
    form = MessageForm()
    
    return render_template('messages_thread.html',
                         conversation=conversation,
                         messages=messages,
                         other_participant=other_participant,
                         transaction=transaction,
                         listing=listing,
                         form=form)


# ============================================
# SEND MESSAGE
# ============================================

@bp.route('/conversation/<int:conversation_id>/send', methods=['POST'])
@login_required
def send_message(conversation_id):
    """Send a message in a conversation"""
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if user is participant
    if conversation.seller_id != current_user.id and conversation.buyer_id != current_user.id:
        flash('You do not have access to this conversation.', 'danger')
        return redirect(url_for('messages.index'))
    
    # Check if conversation is active
    if not conversation.is_active:
        flash('This conversation is no longer active.', 'warning')
        return redirect(url_for('messages.index'))
    
    form = MessageForm()
    
    if form.validate_on_submit():
        content = form.content.data.strip()
        
        if content:
            # Create message
            message = Message(
                conversation_id=conversation.id,
                sender_id=current_user.id,
                content=content
            )
            db.session.add(message)
            
            # Update conversation
            conversation.last_message = content[:200]
            conversation.last_message_at = datetime.utcnow()
            conversation.last_message_sender_id = current_user.id
            conversation.updated_at = datetime.utcnow()
            
            # Increment unread count for recipient
            conversation.increment_unread(current_user.id)
            
            db.session.commit()
            
            # Create notification for recipient
            recipient_id = conversation.seller_id if current_user.id == conversation.buyer_id else conversation.buyer_id
           
            notification = Notification(
                user_id=recipient_id,
                type='new_message',
                title='New Message',
                message=f'New message from {current_user.full_name} regarding {conversation.item.name if conversation.item else "your transaction"}',
                related_type='conversation',
                related_id=conversation.id
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Message sent!', 'success')
    
    return redirect(url_for('messages.thread', conversation_id=conversation.id))


# ============================================
# START NEW CONVERSATION
# ============================================

@bp.route('/start', methods=['GET', 'POST'])
@login_required
def start_conversation():
    """Start a new conversation with a seller about a listing"""
    
    listing_id = request.args.get('listing_id', type=int)
    transaction_id = request.args.get('transaction_id', type=int)
    user_id = request.args.get('user_id', type=int)
    print(listing_id)
    # Determine the recipient
    recipient = None
    listing = None
    transaction = None
    
    if listing_id:
        listing = Listing.query.get_or_404(listing_id)
        recipient = listing.owned_user
        context = 'listing'
    elif transaction_id:
        transaction = Transaction.query.get_or_404(transaction_id)
        if transaction.seller_company_id == current_user.company_id:
            recipient = transaction.buyer_manager
        else:
            recipient = transaction.seller_manager
        context = 'transaction'
    elif user_id:
        recipient = User.query.get_or_404(user_id)
        context = 'direct'
    else:
        flash('No recipient specified.', 'danger')
        return redirect(url_for('messages.index'))
    
    # Check if conversation already exists
    existing_conversation = None
    
    if listing:
        existing_conversation = Conversation.query.filter(
            and_(
                Conversation.item_id == listing.id,
                or_(
                    and_(Conversation.seller_id == current_user.id, Conversation.buyer_id == recipient.id),
                    and_(Conversation.seller_id == recipient.id, Conversation.buyer_id == current_user.id)
                )
            )
        ).first()
    elif transaction:
        existing_conversation = Conversation.query.filter(
            and_(
                Conversation.transaction_id == transaction.id,
                or_(
                    and_(Conversation.seller_id == current_user.id, Conversation.buyer_id == recipient.id),
                    and_(Conversation.seller_id == recipient.id, Conversation.buyer_id == current_user.id)
                )
            )
        ).first()
    else:
        existing_conversation = Conversation.query.filter(
            or_(
                and_(Conversation.seller_id == current_user.id, Conversation.buyer_id == recipient.id),
                and_(Conversation.seller_id == recipient.id, Conversation.buyer_id == current_user.id)
            )
        ).first()
    
    if existing_conversation:
        return redirect(url_for('messages.thread', conversation_id=existing_conversation.id))
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        
        if content and recipient:
            # Determine seller and buyer
            if listing and listing.user_id == current_user.id:
                seller_id = current_user.id
                buyer_id = recipient.id
            elif listing:
                seller_id = recipient.id
                buyer_id = current_user.id
            elif transaction:
                if transaction.seller_manager_id== current_user.id:
                    seller_id = current_user.id
                    buyer_id = recipient.id
                else:
                    seller_id = recipient.id
                    buyer_id = current_user.id
            else:
                # Direct message - set seller as recipient, buyer as current
                seller_id = recipient.id
                buyer_id = current_user.id
            
            # Create conversation
            conversation = Conversation(
                seller_id=seller_id,
                buyer_id=buyer_id,
                item_id=listing.id if listing else None,
                transaction_id=transaction.id if transaction else None
            )
            db.session.add(conversation)
            db.session.flush()
            
            # Create first message
            message = Message(
                conversation_id=conversation.id,
                sender_id=current_user.id,
                content=content
            )
            db.session.add(message)
            
            # Update conversation
            conversation.last_message = content[:200]
            conversation.last_message_at = datetime.utcnow()
            conversation.last_message_sender_id = current_user.id
            conversation.increment_unread(current_user.id)
            
            db.session.commit()
            
            # Create notification
            notification = Notification(
                user_id=recipient.id,
                type='new_conversation',
                title='New Message',
                message=f'{current_user.full_name} started a conversation with you.',
                related_type='conversation',
                related_id=conversation.id
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Conversation started!', 'success')
            return redirect(url_for('messages.thread', conversation_id=conversation.id))
    
    return render_template('start.html', 
                         recipient=recipient, 
                         listing=listing, 
                         transaction=transaction)


# ============================================
# DELETE CONVERSATION
# ============================================

@bp.route('/conversation/<int:conversation_id>/delete', methods=['POST'])
@login_required
def delete_conversation(conversation_id):
    """Delete conversation for current user (soft delete)"""
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if user is participant
    if conversation.seller_id == current_user.id:
        conversation.seller_deleted = True
    elif conversation.buyer_id == current_user.id:
        conversation.buyer_deleted = True
    else:
        flash('You do not have access to this conversation.', 'danger')
        return redirect(url_for('messages.index'))
    
    db.session.commit()
    
    flash('Conversation deleted.', 'success')
    return redirect(url_for('messages.index'))


# ============================================
# API - GET UNREAD COUNT
# ============================================

@bp.route('/unread-count')
@login_required
def unread_count():
    """Get unread message count for current user (for navbar badge)"""
    
    conversations = Conversation.query.filter(
        or_(
            and_(Conversation.seller_id == current_user.id, Conversation.seller_deleted == False),
            and_(Conversation.buyer_id == current_user.id, Conversation.buyer_deleted == False)
        )
    ).all()
    
    unread_count = 0
    for conv in conversations:
        if conv.seller_id == current_user.id:
            unread_count += conv.seller_unread_count
        else:
            unread_count += conv.buyer_unread_count
    
    return jsonify({'unread_count': unread_count})


# ============================================
# API - MARK CONVERSATION AS READ
# ============================================

@bp.route('/conversation/<int:conversation_id>/read', methods=['POST'])
@login_required
def mark_as_read(conversation_id):
    """Mark conversation as read via API"""
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    if conversation.seller_id != current_user.id and conversation.buyer_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    conversation.mark_as_read(current_user.id)
    
    return jsonify({'success': True})