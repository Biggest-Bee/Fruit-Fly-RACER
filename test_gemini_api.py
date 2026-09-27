"""
Test script for Gemini API connection
Run this to verify your API key is working correctly
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

def test_gemini_api():
    """Test the Gemini API connection"""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ Error: Please set your GEMINI_API_KEY in the .env file")
        print("   Edit the .env file and replace 'your_gemini_api_key_here' with your actual key")
        return False
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    try:
        # Test with a simple request
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, this is a test.")
        
        print("✅ Gemini API connection successful!")
        print(f"   Response: {response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Gemini API: {e}")
        print("   Please check your API key and internet connection")
        return False

if __name__ == "__main__":
    print("Testing Gemini API connection...")
    test_gemini_api()