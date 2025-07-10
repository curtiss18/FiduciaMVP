"""
Quick configuration check for SendGrid email setup
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_email_config():
    """Check if email configuration is properly set up"""
    
    print("Checking FiduciaMVP Email Configuration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    checks = []
    
    # 1. SendGrid API Key
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        checks.append(("ERROR", "SENDGRID_API_KEY", "Not found in .env file"))
    elif api_key == "your_sendgrid_api_key_here":
        checks.append(("WARNING", "SENDGRID_API_KEY", "Still using placeholder value"))
    elif not api_key.startswith("SG."):
        checks.append(("WARNING", "SENDGRID_API_KEY", "Doesn't start with 'SG.' - may be invalid"))
    else:
        checks.append(("OK", "SENDGRID_API_KEY", f"Configured (starts with: {api_key[:10]}...)"))
    
    # 2. From Email
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "notifications@fiducia.ai")
    checks.append(("OK", "SENDGRID_FROM_EMAIL", from_email))
    
    # 3. From Name  
    from_name = os.getenv("SENDGRID_FROM_NAME", "Fiducia Compliance System")
    checks.append(("OK", "SENDGRID_FROM_NAME", from_name))
    
    # 4. Check if email service can be imported
    try:
        # Add the project root directory to the path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.services.email_service import email_service
        checks.append(("OK", "Email Service Import", "Successfully imported"))
        
        # Check if client initializes
        if email_service.client is not None:
            checks.append(("OK", "SendGrid Client", "Initialized successfully"))
        else:
            checks.append(("ERROR", "SendGrid Client", "Failed to initialize (check API key)"))
            
    except ImportError as e:
        checks.append(("ERROR", "Email Service Import", f"Failed: {e}"))
    except Exception as e:
        checks.append(("ERROR", "Email Service", f"Error: {e}"))
    
    # Print results
    print("\nConfiguration Check Results:")
    print("-" * 50)
    for status, item, detail in checks:
        status_symbol = "[OK]" if status == "OK" else "[!]" if status == "WARNING" else "[X]"
        print(f"{status_symbol} {item:25} {detail}")
    
    # Count issues
    errors = sum(1 for check in checks if check[0] == "ERROR")
    warnings = sum(1 for check in checks if check[0] == "WARNING")
    
    print("\n" + "=" * 50)
    
    if errors == 0 and warnings == 0:
        print("SUCCESS: Email configuration is ready to use.")
        print("\nNext steps:")
        print("1. Run: python src/test_email.py")
        print("2. Test the full workflow in the advisor portal")
        return True
    elif errors == 0:
        print(f"MOSTLY READY: Configuration has {warnings} warning(s)")
        print("\nRecommendations:")
        print("1. Fix the warnings above for best results")
        print("2. Test with: python src/test_email.py")
        return True
    else:
        print(f"ISSUES FOUND: Configuration has {errors} error(s) and {warnings} warning(s)")
        print("\nRequired fixes:")
        print("1. Set up SendGrid account and get API key")
        print("2. Update SENDGRID_API_KEY in .env file") 
        print("3. Run this check again")
        return False

if __name__ == "__main__":
    check_email_config()
