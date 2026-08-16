import os
from app import app,db
from flask import render_template,request
from app.auth.models import Company, User
from app.listings.models import Category,Item, Quality_attributes
from app.transactions.models import Transaction


from flask_login import login_required,current_user
from sqlalchemy import and_, desc, func,or_
from datetime import datetime, timedelta

from app.offers.models import Offer

@app.route("/")
def home():

    recent_listings=Item.query.filter_by(is_featured=True).order_by(desc(Item.created_at)).limit(4).all()
    categories=Category.query.all()
    featured_companies=Company.query.order_by(desc(Company.rating_avg)).limit(5).all()
    total_listings=Item.query.count()
    total_companies=Company.query.count()
    total_transactions=Transaction.query.count()
    return render_template('home.html',recent_listings=recent_listings,categories=categories,featured_companies=featured_companies,total_companies=total_companies,total_listings=total_listings,total_transactions=total_transactions)

@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/teams")
def teams():
    
    teams=User.query.filter_by(company_id=current_user.company_id).all()

    return render_template('teams.html',teams=teams)

@app.route('/dashboard')
@login_required
def dashboard():
  
    company = current_user.owned_company
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # ========== STATS CARDS ==========
    # Active listings
    active_listings = Item.query.filter_by(
        company_id=company.id,
        status='active'
    ).filter(Item.expires_at > datetime.utcnow()).count()
    
    # Pending offers (received)
    pending_offers_received = Offer.query.join(Item).filter(
        Item.company_id == company.id,
        Offer.status == 'pending'
    ).count()
    
    # Pending offers (sent by this company)
    pending_offers_sent = Offer.query.filter_by(
        sender_company_id=company.id,
        status='pending'
    ).count()
    
    # Active transactions
    active_transactions = Transaction.query.filter(
        and_(
            (Transaction.seller_company_id == company.id) | 
            (Transaction.buyer_company_id == company.id),
            Transaction.status.in_(['pending', 'confirmed', 'in_transit'])
        )
    ).count()
    
    # Completed transactions (this month)
    completed_transactions = Transaction.query.filter(
        and_(
            (Transaction.seller_company_id == company.id) | 
            (Transaction.buyer_company_id == company.id),
            Transaction.status == 'completed',
            Transaction.completed_at >= month_ago
        )
    ).count()
    
    # Total revenue (from completed sales)
    total_revenue = company.total_revenue
    
    # Average rating
    """avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.company_id == company.id
    ).scalar() or 0
    """
    # ========== CHARTS DATA ==========
    # Last 7 days listings
    listings_weekly = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = Item.query.filter(
            Item.company_id == company.id,
            func.date(Item.created_at) == date
        ).count()
        listings_weekly.append({
            'date': date.strftime('%a'),
            'count': count
        })
    
    # Last 7 days offers
    offers_weekly = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        received = Offer.query.join(Item).filter(
            Item.company_id == company.id,
            func.date(Offer.created_at) == date
        ).count()
        sent = Offer.query.filter(
            Offer.sender_company_id == company.id,
            func.date(Offer.created_at) == date
        ).count()
        offers_weekly.append({
            'date': date.strftime('%a'),
            'received': received,
            'sent': sent
        })
    
    # Monthly transactions
    monthly_transactions = []
    for i in range(5, -1, -1):
        month = today.replace(day=1) - timedelta(days=30 * i)
        month_end = (month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        count = Transaction.query.filter(
            and_(
                (Transaction.seller_company_id == company.id) | 
                (Transaction.buyer_company_id == company.id),
                Transaction.status == 'completed',
                Transaction.completed_at >= month,
                Transaction.completed_at <= month_end
            )
        ).count()
        
        monthly_transactions.append({
            'month': month.strftime('%b'),
            'count': count
        })
    
    # Category breakdown
    category_breakdown = db.session.query(
        Category.name,
        func.count(Item.id).label('count')
    ).join(Item).filter(
        Item.company_id == company.id,
        Item.status == 'active'
    ).group_by(Category.name).all()
    
    categories = [{'name': cat[0], 'count': cat[1]} for cat in category_breakdown]
    
    # ========== RECENT ACTIVITIES ==========
    # Recent listings
    recent_listings = Item.query.filter_by(
        company_id=company.id
    ).order_by(desc(Item.created_at)).limit(5).all()
    
    # Recent offers received
    recent_offers_received = Offer.query.join(Item).filter(
        Item.company_id == company.id
    ).order_by(desc(Offer.created_at)).limit(5).all()
    
    # Recent transactions
    recent_transactions = Transaction.query.filter(
        (Transaction.seller_company_id == company.id) | 
        (Transaction.buyer_company_id == company.id)
    ).order_by(desc(Transaction.created_at)).limit(5).all()
    
    
    # Completion rate
    total_offers = Offer.query.join(Item).filter(
        Item.company_id == company.id
    ).count()
    
    accepted_offers = Offer.query.join(Item).filter(
        Item.company_id == company.id,
        Offer.status == 'accepted'
    ).count()
    
    completion_rate = round((accepted_offers / total_offers * 100) if total_offers > 0 else 0, 1)
    
    # Listing views
    total_views = db.session.query(func.sum(Item.views)).filter(
        Item.company_id == company.id
    ).scalar() or 0
    
    avg_views_per_listing = round(total_views / active_listings if active_listings > 0 else 0, 1)
    
    return render_template('dashboard.html',
                         # Stats
                         active_listings=active_listings,
                         pending_offers_received=pending_offers_received,
                         pending_offers_sent=pending_offers_sent,
                         active_transactions=active_transactions,
                         completed_transactions=completed_transactions,
                         total_revenue=total_revenue,
                        
                         
                         # Charts
                         listings_weekly=listings_weekly,
                         offers_weekly=offers_weekly,
                         monthly_transactions=monthly_transactions,
                         categories=categories,
                         
                         # Recent activity
                         recent_listings=recent_listings,
                         recent_offers_received=recent_offers_received,
                         recent_transactions=recent_transactions,
                         
                         
                         
                         # Company metrics
                         
                         completion_rate=completion_rate,
                         total_views=total_views,
                         avg_views_per_listing=avg_views_per_listing)




