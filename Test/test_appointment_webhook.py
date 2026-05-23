import requests
import os
import sys
import json
from datetime import datetime, timedelta
import argparse
import calendar

# Add parent directory to path to allow imports from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Arabic day names
ARABIC_DAYS = {
    0: "الاثنين",    # Monday
    2: "الأربعاء",   # Wednesday
    4: "الجمعة"     # Friday
}

def generate_available_days_and_slots(num_weeks=4):
    """Generate available days, dates and time slots for testing"""
    available_days = {}
    today = datetime.now()
    
    # Start from next day
    current_date = today + timedelta(days=1)
    
    # Generate data for specified number of weeks
    for _ in range(num_weeks * 7):
        # Only include Monday, Wednesday, Friday
        if current_date.weekday() in [0, 2, 4]:  # Mon, Wed, Fri
            day_name = ARABIC_DAYS[current_date.weekday()]
            date_str = current_date.strftime('%Y-%m-%d')
            formatted_date = current_date.strftime('%d/%m/%Y')
            
            # If this day doesn't exist in our dict yet, add it
            if day_name not in available_days:
                available_days[day_name] = []
                
            # Add this date to the day
            time_slots = []
            
            # Generate time slots (9:00 AM to 5:00 PM, every hour)
            for hour in range(9, 18):
                # Skip lunch break
                if hour != 13:
                    # Morning slots
                    if hour < 13:
                        time_slots.append(f"{hour:02d}:00 صباحاً")
                        time_slots.append(f"{hour:02d}:30 صباحاً")
                    # Afternoon slots  
                    else:
                        time_slots.append(f"{hour:02d}:00 مساءً")
                        time_slots.append(f"{hour:02d}:30 مساءً") 
            
            available_days[day_name].append({
                "date": date_str,
                "formatted_date": formatted_date,
                "time_slots": time_slots
            })
            
        # Move to next day
        current_date += timedelta(days=1)
    
    return available_days

def interactive_appointment_selection():
    """Interactive UI for selecting appointment day, date and time"""
    available_days = generate_available_days_and_slots()
    
    print("\n=== حجز موعد جديد ===\n")
    
    # Step 1: Choose day of week
    print("اختر اليوم المناسب:\n")
    days = list(available_days.keys())
    for i, day in enumerate(days):
        print(f"{i+1}. {day}")
    
    day_choice = 0
    while day_choice < 1 or day_choice > len(days):
        try:
            day_choice = int(input("\nاختيارك (رقم): "))
            if day_choice < 1 or day_choice > len(days):
                print("اختيار غير صالح. الرجاء المحاولة مرة أخرى.")
        except ValueError:
            print("الرجاء إدخال رقم.")
    
    selected_day = days[day_choice-1]
    print(f"\nتم اختيار يوم: {selected_day}")
    
    # Step 2: Choose specific date
    print("\nاختر التاريخ المناسب:\n")
    dates = available_days[selected_day]
    for i, date_info in enumerate(dates):
        print(f"{i+1}. {date_info['formatted_date']}")
    
    date_choice = 0
    while date_choice < 1 or date_choice > len(dates):
        try:
            date_choice = int(input("\nاختيارك (رقم): "))
            if date_choice < 1 or date_choice > len(dates):
                print("اختيار غير صالح. الرجاء المحاولة مرة أخرى.")
        except ValueError:
            print("الرجاء إدخال رقم.")
    
    selected_date = dates[date_choice-1]
    print(f"\nتم اختيار تاريخ: {selected_date['formatted_date']}")
    
    # Step 3: Choose time slot
    print("\nاختر الوقت المناسب:\n")
    time_slots = selected_date['time_slots']
    
    # Display time slots in rows of 3
    for i in range(0, len(time_slots), 3):
        row = time_slots[i:i+3]
        print(" | ".join([f"{i+j+1}. {slot}" for j, slot in enumerate(row)]))
    
    time_choice = 0
    while time_choice < 1 or time_choice > len(time_slots):
        try:
            time_choice = int(input("\nاختيارك (رقم): "))
            if time_choice < 1 or time_choice > len(time_slots):
                print("اختيار غير صالح. الرجاء المحاولة مرة أخرى.")
        except ValueError:
            print("الرجاء إدخال رقم.")
    
    selected_time = time_slots[time_choice-1]
    print(f"\nتم اختيار وقت: {selected_time}")
    
    # Final confirmation
    print("\n=== ملخص الحجز ===")
    print(f"اليوم: {selected_day}")
    print(f"التاريخ: {selected_date['formatted_date']}")
    print(f"الوقت: {selected_time}")
    
    return {
        "day": selected_day,
        "date": selected_date['date'],
        "formatted_date": selected_date['formatted_date'],
        "time": selected_time,
        "full_appointment": f"{selected_day} {selected_date['formatted_date']} {selected_time}"
    }

def test_webhook(webhook_url=None, tag="get_available_slots", interactive=False):
    """Send test requests to your appointment webhook to verify functionality"""
    
    # Get base URL from environment or command line
    if not webhook_url:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        webhook_url = f"https://{project_id}.uc.r.appspot.com/appointment_webhook"
    
    print(f"Testing appointment webhook at: {webhook_url}")
    
    # Parameters for request
    parameters = {
        "days_ahead": 28,  # 4 weeks
        "service_id": None
    }
    
    # If interactive, let user select appointment
    if interactive:
        appointment = interactive_appointment_selection()
        
        if tag == "book_appointment":
            parameters.update({
                "selected_day": appointment["day"],
                "selected_date": appointment["date"],
                "selected_time": appointment["time"],
                "appointment_string": appointment["full_appointment"]
            })
    
    # Create test payload that mimics Dialogflow CX webhook request format
    test_payload = {
        "fulfillmentInfo": {
            "tag": tag
        },
        "sessionInfo": {
            "parameters": parameters
        }
    }
    
    print(f"\nTesting webhook with tag '{tag}'")
    print(f"Request payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        # Send the test request
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            webhook_url,
            headers=headers,
            json=test_payload,
            timeout=30  # Longer timeout for API calls
        )
        
        # Check response
        print(f"\nResponse status code: {response.status_code}")
        if response.status_code == 200:
            try:
                response_data = response.json()
                print("\nWebhook Response:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                # Verify if the response has the expected format
                if 'fulfillmentResponse' in response_data and 'messages' in response_data['fulfillmentResponse']:
                    print("\n✅ Response format is correct!")
                    
                    # Check for rich content (buttons)
                    has_buttons = False
                    for msg in response_data['fulfillmentResponse']['messages']:
                        if 'payload' in msg and 'richContent' in msg['payload']:
                            has_buttons = True
                            print("✅ Response includes button options!")
                    
                    if not has_buttons:
                        print("❓ No button options found in response.")
                else:
                    print("\n❌ Response format is incorrect. Expected 'fulfillmentResponse' with 'messages'.")
            except json.JSONDecodeError:
                print("\n❌ Response is not valid JSON:")
                print(response.text)
        else:
            print("\n❌ Request failed:")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")

def test_webhook_availability(webhook_url=None):
    """Test if the webhook is available at all"""
    # Get base URL from environment or command line
    if not webhook_url:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        base_url = f"https://{project_id}.uc.r.appspot.com"
    else:
        base_url = webhook_url.split('/appointment_webhook')[0]
    
    print(f"Testing webhook availability on: {base_url}")
    
    # Test the test endpoint first
    test_url = f"{base_url}/test_webhook"
    try:
        print(f"\nTesting diagnostic endpoint: {test_url}")
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Test endpoint is working")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Test endpoint returned status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error accessing test endpoint: {str(e)}")
    
    # Now test the actual webhook endpoint with a GET request
    webhook_url = f"{base_url}/appointment_webhook"
    try:
        print(f"\nTesting webhook with GET (should fail gracefully): {webhook_url}")
        response = requests.get(webhook_url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error accessing webhook endpoint: {str(e)}")

def test_local_webhook(port=5000, tag="get_available_slots", interactive=False):
    """Test webhook on local development server"""
    local_url = f"http://localhost:{port}/appointment_webhook"
    test_webhook(local_url, tag, interactive)

def test_deployed_webhook(tag="get_available_slots", interactive=False):
    """Test webhook on deployed app"""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    deployed_url = f"https://{project_id}.uc.r.appspot.com/appointment_webhook"
    test_webhook(deployed_url, tag, interactive)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test the appointment webhook')
    parser.add_argument('--local', action='store_true', help='Test local development server')
    parser.add_argument('--port', type=int, default=5000, help='Port for local testing')
    parser.add_argument('--tag', type=str, default='get_available_slots', help='Tag to test')
    parser.add_argument('--check', action='store_true', help='Check if webhook is available')
    parser.add_argument('--interactive', action='store_true', help='Use interactive appointment selection')
    parser.add_argument('--book', action='store_true', help='Test booking flow (combines with --interactive)')
    args = parser.parse_args()
    
    if args.check:
        if args.local:
            test_webhook_availability(f"http://localhost:{args.port}")
        else:
            test_webhook_availability()
    else:
        # Set tag to book_appointment if --book is specified
        if args.book:
            args.tag = "book_appointment"
            args.interactive = True  # Booking requires interactive mode
            
        if args.local:
            test_local_webhook(args.port, args.tag, args.interactive)
        else:
            test_deployed_webhook(args.tag, args.interactive)