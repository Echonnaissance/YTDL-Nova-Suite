"""
Security Key Generator
Generates secure random keys for SECRET_KEY and API_KEY
"""
import secrets

def generate_keys():
    """Generate secure random keys"""
    print("=" * 80)
    print("Security Key Generator")
    print("=" * 80)
    print()
    print("Copy these values to your .env file:")
    print()
    print("-" * 80)
    print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
    print(f"API_KEY={secrets.token_urlsafe(32)}")
    print("-" * 80)
    print()
    print("IMPORTANT:")
    print("1. Copy these values to your .env file")
    print("2. Never commit .env to version control")
    print("3. Keep these keys secret and secure")
    print("4. Generate new keys for each environment (dev, staging, production)")
    print()
    print("=" * 80)

if __name__ == "__main__":
    generate_keys()
