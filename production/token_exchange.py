# production/token_exchange.py

import os
import sys
from google_auth_oauthlib.flow import Flow

# Required for http redirect
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# The exact parameters from the worker logs
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
REDIRECT_URI = "http://localhost:8080/"

def main():
    if len(sys.argv) < 2:
        print("Usage: python token_exchange.py <AUTH_CODE>")
        return

    auth_code = sys.argv[1]
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    print(f"Fetching token for code: {auth_code[:10]}...")
    try:
        flow.fetch_token(code=auth_code)
        
        credentials = flow.credentials
        with open('token.json', 'w') as token_file:
            token_file.write(credentials.to_json())
            
        print("Successfully created token.json!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
