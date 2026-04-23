"""
Verification script to check if weekly summary calculations are correct.
Run this after generating test data to verify the numbers match.
"""
import requests
from datetime import datetime, timedelta

from app.core.config import build_api_url

BASE_URL = build_api_url("/api/training")
USER_ID = 1  # Change to your test user ID

def generate_test_sessions(num_sessions=10):
    """Generate test sessions spread across last 7 days"""
    print(f"\n📊 Generating {num_sessions} test sessions...")
    response = requests.post(f"{BASE_URL}/dev/generate-sessions/{USER_ID}?num_sessions={num_sessions}")
    data = response.json()
    print(f"✅ Generated: {data.get('sessions_generated')} sessions ({data.get('sessions_generated', 0) * 4} tasks)")
    return data

def get_weekly_summary():
    """Get weekly summary from API"""
    print(f"\n📈 Fetching weekly summary...")
    response = requests.get(f"{BASE_URL}/weekly-summary/{USER_ID}")
    return response.json()

def get_all_sessions():
    """Get all training sessions to manually verify"""
    print(f"\n🔍 Fetching all sessions for manual verification...")
    response = requests.get(f"{BASE_URL}/history/{USER_ID}")
    return response.json()

def verify_calculations(summary, sessions):
    """Manually verify the calculations"""
    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)
    
    # Filter sessions from last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_sessions = [
        s for s in sessions 
        if datetime.fromisoformat(s['created_at'].replace('Z', '+00:00')) > seven_days_ago
    ]
    
    print(f"\n📅 Sessions in last 7 days: {len(recent_sessions)}")
    print(f"   API says: {summary.get('total_sessions', 0)}")
    print(f"   Match: {'✅' if len(recent_sessions) == summary.get('total_sessions', 0) else '❌'}")
    
    if recent_sessions:
        # Calculate average score
        avg_score = sum(s['score'] for s in recent_sessions) / len(recent_sessions)
        api_avg_score = summary.get('average_score', 0)
        print(f"\n⭐ Average Score:")
        print(f"   Calculated: {avg_score:.1f}")
        print(f"   API says: {api_avg_score:.1f}")
        print(f"   Match: {'✅' if abs(avg_score - api_avg_score) < 0.1 else '❌'}")
        
        # Calculate average accuracy
        avg_accuracy = sum(s['accuracy'] for s in recent_sessions) / len(recent_sessions)
        api_avg_accuracy = summary.get('average_accuracy', 0)
        print(f"\n🎯 Average Accuracy:")
        print(f"   Calculated: {avg_accuracy:.1f}%")
        print(f"   API says: {api_avg_accuracy:.1f}%")
        print(f"   Match: {'✅' if abs(avg_accuracy - api_avg_accuracy) < 0.1 else '❌'}")
        
        # Calculate total time
        total_time = sum(s.get('duration', 0) for s in recent_sessions)
        api_total_time = summary.get('total_time_minutes', 0)
        print(f"\n⏱️  Total Time:")
        print(f"   Calculated: {total_time} minutes")
        print(f"   API says: {api_total_time} minutes")
        print(f"   Match: {'✅' if total_time == api_total_time else '❌'}")
        
        # Daily activity
        daily_counts = summary.get('daily_activity', [])
        print(f"\n📊 Daily Activity (last 7 days):")
        for day in daily_counts:
            print(f"   {day['day']}: {day['count']} sessions")
        
        # Most improved
        most_improved = summary.get('most_improved_domain', {})
        if most_improved:
            print(f"\n🚀 Most Improved Domain:")
            print(f"   {most_improved.get('domain')}: +{most_improved.get('improvement', 0):.1f}")
    
    print("\n" + "="*60 + "\n")

def main():
    print("🧪 Weekly Summary Data Verification Tool")
    print("="*60)
    
    # Step 1: Generate test data
    choice = input("\nGenerate new test sessions? (y/n): ")
    if choice.lower() == 'y':
        num = input("How many sessions to generate? (default 10): ")
        num = int(num) if num else 10
        generate_test_sessions(num)
    
    # Step 2: Get weekly summary
    summary = get_weekly_summary()
    
    # Step 3: Get all sessions for verification
    all_sessions = get_all_sessions()
    
    # Step 4: Verify calculations
    verify_calculations(summary, all_sessions)
    
    print("💡 Tips:")
    print("   - Check the frontend weekly summary card matches these numbers")
    print("   - Daily activity chart should show the same counts")
    print("   - Most improved domain should match")

if __name__ == "__main__":
    main()
