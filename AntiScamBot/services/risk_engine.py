from typing import Dict

def calculate_scammer_risk_score(scammer_data: Dict) -> Dict:
    """Calculate risk score for a scammer."""
    report_count = scammer_data.get('report_count', 0)
    reporter_count = scammer_data.get('reporter_count', 0)
    total_amount = scammer_data.get('total_amount', 0)
    
    # Base score from report count
    score = report_count * 10
    
    # Bonus for unique reporters
    score += reporter_count * 5
    
    # Bonus for high amount
    if total_amount > 10000:
        score += 30
    elif total_amount > 5000:
        score += 20
    elif total_amount > 1000:
        score += 10
    
    # Calculate risk level
    if score >= 80:
        risk_level = "🔴 CRITICAL"
    elif score >= 50:
        risk_level = "🔴 HIGH"
    elif score >= 30:
        risk_level = "🟡 MEDIUM"
    elif score >= 10:
        risk_level = "🟠 LOW"
    else:
        risk_level = "🟢 MINIMAL"
    
    return {
        'score': score,
        'risk_level': risk_level,
        'recommendation': get_recommendation(score),
        'confidence': min(score / 100, 1.0)  # 0.0 to 1.0
    }

def get_recommendation(score: int) -> str:
    """Get recommendation based on risk score."""
    if score >= 50:
        return "DO NOT TRADE - High risk of scam"
    elif score >= 30:
        return "Extreme caution required - Verify thoroughly"
    elif score >= 10:
        return "Proceed with caution - Verify identity"
    else:
        return "Low risk - Standard verification recommended"

def aggregate_scammer_data(scammer_reports: list) -> Dict:
    """Aggregate data from multiple reports about same scammer."""
    if not scammer_reports:
        return {}
    
    unique_reporters = set()
    total_amount = 0
    
    for report in scammer_reports:
        unique_reporters.add(report['reporter_id'])
        total_amount += report.get('amount', 0)
    
    return {
        'report_count': len(scammer_reports),
        'reporter_count': len(unique_reporters),
        'total_amount': total_amount,
        'first_report_date': min(r['created_at'] for r in scammer_reports),
        'last_report_date': max(r['created_at'] for r in scammer_reports)
    }
