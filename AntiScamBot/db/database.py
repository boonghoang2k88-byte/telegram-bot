from datetime import datetime, timedelta
from sqlalchemy import and_, func
from db.session import get_db_session
from db.models import User, Scammer, Report, Statistics

def save_report(report_data: dict) -> bool:
    """Save report to database."""
    try:
        session = next(get_db_session())
        
        # Check if scammer already exists
        scammer = session.query(Scammer).filter(
            (Scammer.username == report_data['scammer_username']) |
            (Scammer.binance_id == report_data['scammer_id'])
        ).first()
        
        if not scammer:
            # Create new scammer
            scammer = Scammer(
                name=report_data['scammer_name'],
                username=report_data['scammer_username'],
                telegram_link=report_data['scammer_link'],
                binance_id=report_data.get('scammer_id'),
                report_count=1,
                reporter_count=1,
                total_amount=report_data.get('amount', 0),
                first_reported=datetime.utcnow(),
                last_reported=datetime.utcnow()
            )
            session.add(scammer)
            session.flush()  # Get scammer id
        else:
            # Update existing scammer
            scammer.report_count += 1
            scammer.total_amount += report_data.get('amount', 0)
            scammer.last_reported = datetime.utcnow()
            
            # Check if this is a new reporter
            existing_reporter = session.query(Report).filter(
                and_(
                    Report.scammer_id == scammer.id,
                    Report.reporter_id == report_data['reporter_id']
                )
            ).first()
            
            if not existing_reporter:
                scammer.reporter_count += 1
        
        # Create report
        report = Report(
            reporter_id=report_data['reporter_id'],
            reporter_username=report_data.get('reporter_username'),
            scammer_id=scammer.id,
            scammer_name=report_data['scammer_name'],
            scammer_username=report_data['scammer_username'],
            scammer_link=report_data['scammer_link'],
            binance_id=report_data.get('scammer_id'),
            amount=report_data.get('amount', 0),
            status='confirmed'
        )
        session.add(report)
        
        # Update user report count
        user = session.query(User).filter(User.telegram_id == report_data['reporter_id']).first()
        if user:
            user.report_count += 1
            user.last_active = datetime.utcnow()
        else:
            # Create user if not exists
            user = User(
                telegram_id=report_data['reporter_id'],
                username=report_data.get('reporter_username'),
                report_count=1
            )
            session.add(user)
        
        session.commit()
        return True
        
    except Exception as e:
        print(f"Error saving report: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_scammer_details(identifier: str, identifier_type: str = 'username') -> dict:
    """Get scammer details by identifier."""
    try:
        session = next(get_db_session())
        
        if identifier_type == 'username':
            scammer = session.query(Scammer).filter(Scammer.username == identifier).first()
        elif identifier_type == 'binance_id':
            scammer = session.query(Scammer).filter(Scammer.binance_id == identifier).first()
        elif identifier_type == 'telegram_link':
            scammer = session.query(Scammer).filter(Scammer.telegram_link == identifier).first()
        else:
            scammer = session.query(Scammer).filter(Scammer.name == identifier).first()
        
        if scammer:
            # Get all reports for this scammer
            reports = session.query(Report).filter(Report.scammer_id == scammer.id).all()
            
            return {
                'id': scammer.id,
                'name': scammer.name,
                'username': scammer.username,
                'telegram_link': scammer.telegram_link,
                'binance_id': scammer.binance_id,
                'report_count': scammer.report_count,
                'reporter_count': scammer.reporter_count,
                'total_amount': scammer.total_amount,
                'first_reported': scammer.first_reported,
                'last_reported': scammer.last_reported,
                'reports': [
                    {
                        'reporter_id': r.reporter_id,
                        'amount': r.amount,
                        'created_at': r.created_at
                    }
                    for r in reports[:10]  # Limit to 10 recent reports
                ]
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting scammer details: {e}")
        return None
    finally:
        session.close()

def get_scam_statistics() -> dict:
    """Get overall scam statistics."""
    try:
        session = next(get_db_session())
        
        total_reports = session.query(func.count(Report.id)).scalar() or 0
        total_scammers = session.query(func.count(Scammer.id)).scalar() or 0
        total_reporters = session.query(func.count(func.distinct(Report.reporter_id))).scalar() or 0
        total_amount = session.query(func.sum(Report.amount)).scalar() or 0
        
        # Today's statistics
        today = datetime.utcnow().date()
        reports_today = session.query(func.count(Report.id)).filter(
            func.date(Report.created_at) == today
        ).scalar() or 0
        
        return {
            'total_reports': total_reports,
            'total_scammers': total_scammers,
            'unique_reporters': total_reporters,
            'total_amount': total_amount,
            'reports_today': reports_today
        }
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {
            'total_reports': 0,
            'total_scammers': 0,
            'unique_reporters': 0,
            'total_amount': 0,
            'reports_today': 0
        }
    finally:
        session.close()

def get_user_reports_today(user_id: int) -> list:
    """Get user's reports from today."""
    try:
        session = next(get_db_session())
        
        today = datetime.utcnow().date()
        reports = session.query(Report).filter(
            and_(
                Report.reporter_id == user_id,
                func.date(Report.created_at) == today
            )
        ).all()
        
        return reports
        
    except Exception as e:
        print(f"Error getting user reports: {e}")
        return []
    finally:
        session.close()

def get_top_scammers(limit: int = 10) -> list:
    """Get top scammers by report count."""
    try:
        session = next(get_db_session())
        
        scammers = session.query(Scammer).order_by(
            Scammer.report_count.desc()
        ).limit(limit).all()
        
        return [
            {
                'id': s.id,
                'name': s.name,
                'username': s.username,
                'report_count': s.report_count,
                'reporter_count': s.reporter_count,
                'total_amount': s.total_amount
            }
            for s in scammers
        ]
        
    except Exception as e:
        print(f"Error getting top scammers: {e}")
        return []
    finally:
        session.close()
