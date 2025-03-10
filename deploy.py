import os
import subprocess
from dotenv import load_dotenv

def prepare_deployment():
    """Prepare the application for deployment"""
    print("Preparing deployment...")
    
    # Load environment variables
    load_dotenv()
    
    # Clean and generate requirements.txt
    print("Generating clean requirements.txt...")
    with open("requirements.txt", "w") as f:
        f.write("""flask==2.0.1
werkzeug==2.0.1
requests==2.31.0
google-cloud-dialogflow-cx==1.24.0
python-dotenv==0.21.0
flask-admin==1.6.1
pymongo==4.6.1
flask-login==0.6.3
bcrypt==4.1.2
APScheduler==3.10.1
gunicorn==20.1.0
pydantic-settings==2.1.0
google-cloud-storage==2.14.0""")
    
    # Ensure service account file exists
    if not os.path.exists('service_account.json'):
        raise FileNotFoundError("service_account.json is missing!")
    
    # Create .gcloudignore
    print("Creating .gcloudignore...")
    with open('.gcloudignore', 'w') as f:
        f.write("""
.gcloudignore
.git
.gitignore
__pycache__/
*.pyc
.env
.venv/
venv/
ENV/
test_*.py
*.md
deploy.*
""")
    
    print("\nDeployment preparation completed!")
    print("\nNext steps:")
    print("1. Run: deploy.bat")
    print("2. Follow the prompts to complete deployment")

if __name__ == "__main__":
    prepare_deployment()
