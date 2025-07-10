"""
Test script for SendGrid email service
Run this to verify email integration is working
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root directory to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.services.email_service import email_service

async def test_email_service():
    """Test the email service functionality"""
    
    print("Testing Fiducia Email Service")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        print("[X] SENDGRID_API_KEY not found in environment variables")
        print("Please update your .env file with your SendGrid API key")
        return False
    elif api_key == "your_sendgrid_api_key_here":
        print("[X] SENDGRID_API_KEY is still the placeholder value")
        print("Please replace with your actual SendGrid API key")
        return False
    else:
        print("[OK] SendGrid API Key found")
    
    # Check if email service initializes
    try:
        if email_service.client is None:
            print("[X] Email service failed to initialize")
            return False
        print("[OK] Email service initialized successfully")
    except Exception as e:
        print(f"[X] Email service initialization error: {e}")
        return False
    
    # Get test email address
    test_email = input("\nEnter your email address for testing: ").strip()
    if not test_email or "@" not in test_email:
        print("[X] Invalid email address")
        return False
    
    print(f"\nSending test email to: {test_email}")
    print("This may take a few seconds...")
    
    # Send test review notification
    try:
        success = await email_service.send_review_notification(
            to_email=test_email,
            content_title="Test Content - Social Media Post",
            content_type="social_post", 
            advisor_id="test_advisor_123",
            review_url="http://localhost:3003/review/test-token-123",
            notes="This is a test email to verify the SendGrid integration is working properly."
        )
        
        if success:
            print("[OK] Test email sent successfully!")
            print("\nCheck your email inbox (and spam folder) for the test message")
            print("The email should contain a review link and professional formatting")
            
            # Test approval notification too
            print("\nSending test approval notification...")
            approval_success = await email_service.send_approval_notification(
                to_email=test_email,
                content_title="Test Content - Social Media Post",
                status="approved",
                reviewer_feedback="This test content looks great! The messaging is clear and compliant."
            )
            
            if approval_success:
                print("[OK] Test approval email sent successfully!")
                print("\nBoth email types are working correctly!")
            else:
                print("[X] Test approval email failed")
                
        else:
            print("[X] Test email failed to send")
            print("Check the console logs for error details")
            return False
            
    except Exception as e:
        print(f"[X] Error sending test email: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("[OK] Email service test completed successfully!")
    print("\nNext steps:")
    print("1. Check your email for the test messages")
    print("2. Try submitting content through the advisor portal")
    print("3. CCO should receive professional review notification")
    
    return True

if __name__ == "__main__":
    print("Starting Fiducia Email Service Test")
    
    # Run the test
    try:
        result = asyncio.run(test_email_service())
        if result:
            print("\nAll tests passed! Email integration is ready.")
        else:
            print("\nSome tests failed. Check configuration and try again.")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
