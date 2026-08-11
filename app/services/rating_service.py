from app.auth.models import Review, Company
from app import db
from app.services.notification_service import NotificationService

class RatingService:
    """Service for managing company ratings"""
    
    @staticmethod
    def update_company_rating(company_id):
        """
        Update rating for a specific company.
        This is the main function to call when a review is added/updated/deleted.
        """
        company = Company.query.get(company_id)
        if not company:
            return None
        
        # Get all approved reviews
        reviews = Review.query.filter_by(
            company_id=company_id,
            is_approved=True,
            is_public=True
        ).all()
        
        total_reviews = len(reviews)
        
        if total_reviews == 0:
            company.rating_avg = 0
            company.total_reviews = 0
            company.rating_distribution = {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
            db.session.commit()
            return company.get_rating_stats()
        
        # Calculate average
        total_rating = sum(r.rating for r in reviews)
        avg_rating = total_rating / total_reviews
        
        # Calculate distribution
        distribution = {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
        for review in reviews:
            rating_key = str(review.rating)
            if rating_key in distribution:
                distribution[rating_key] += 1
        
        # Update company
        old_rating = company.rating_avg
        company.rating_avg = round(avg_rating, 2)
        company.total_reviews = total_reviews
        company.rating_distribution = distribution
        
        db.session.commit()
        
        # Check if rating changed significantly
        if old_rating and abs(float(old_rating) - float(company.rating_avg)) >= 0.5:
            # Notify company owner about rating change
            owner = company.users.filter_by(role='owner' or 'admin').first()
            if owner:
                NotificationService.create_notification(
                    user_id=owner.id,
                    notification_type='rating_updated',
                    title='Rating Updated',
                    message=f'Your company rating is now {company.rating_avg:.1f}⭐ based on {company.total_reviews} reviews.',
                    priority='normal'
                )
        
        
    
    @staticmethod
    def update_rating_on_review_change(review_id, action='add'):
        """
        Update company rating when a review is added, updated, or deleted.
        """
        review = Review.query.get(review_id)
        if not review:
            return None
        
        return RatingService.update_company_rating(review.company_id)
    
    @staticmethod
    def bulk_update_ratings():
        """
        Bulk update all company ratings (useful for migration or data fixes).
        """
        companies = Company.query.all()
        results = []
        
        for company in companies:
            stats = RatingService.update_company_rating(company.id)
            results.append({
                'company_id': company.id,
                'company_name': company.name,
                'stats': stats
            })
        
        return results
    
    @staticmethod
    def get_top_rated_companies(limit=10, min_reviews=5):
        """
        Get top rated companies with minimum review count.
        """
        companies = Company.query.filter(
            Company.total_reviews >= min_reviews,
            Company.is_active == True
        ).order_by(
            Company.rating_avg.desc()
        ).limit(limit).all()
        
        return companies
    
    @staticmethod
    def get_rating_summary(company_id):
        """Get complete rating summary for display"""
        company = Company.query.get(company_id)
        if not company:
            return None
        
        return {
            'average': float(company.rating_avg) if company.rating_avg else 0,
            'total': company.total_reviews,
            'distribution': company.rating_distribution or {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0},
            'percentages': company.get_rating_percentages(),
            'badge': company.get_rating_badge()
        }