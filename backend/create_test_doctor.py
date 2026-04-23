"""Create a test doctor account for testing the doctor portal."""

import requests
import json

from app.core.config import build_api_url

# Doctor registration data
doctor_data = {
    "email": "dr.smith@neurobloom.test",
    "password": "TestDoctor123!",
    "full_name": "Dr. John Smith",
    "license_number": "MD-12345-NY",
    "specialization": "Neurology",
    "institution": "NeuroBloom Research Center"
}

# API endpoint
url = build_api_url("/api/auth/doctor/register")

try:
    # Send registration request
    print("Creating test doctor account...")
    print(f"Email: {doctor_data['email']}")
    print(f"Name: {doctor_data['full_name']}")
    print(f"Specialization: {doctor_data['specialization']}\n")
    
    response = requests.post(url, json=doctor_data)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Doctor account created successfully!")
        print(f"\nDoctor ID: {result.get('id')}")
        print(f"Email: {result.get('email')}")
        print(f"Full Name: {result.get('full_name')}")
        print(f"License: {result.get('license_number')}")
        print(f"Specialization: {result.get('specialization')}")
        print(f"Institution: {result.get('institution')}")
        print(f"Active: {result.get('is_active')}")
        print(f"Verified: {result.get('is_verified')}")
        
        print("\n" + "="*60)
        print("TEST CREDENTIALS:")
        print("="*60)
        print(f"Email: {doctor_data['email']}")
        print(f"Password: {doctor_data['password']}")
        print("="*60)
        
    else:
        print(f"✗ Registration failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("✗ Error: Could not connect to the backend server.")
    print(f"Make sure the server is running on {build_api_url()}")
except Exception as e:
    print(f"✗ Error: {str(e)}")
