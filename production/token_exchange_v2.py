# production/token_exchange_v2.py

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Required for http redirect
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def main():
    # This approach uses the same logic as GmailHandler's _get_new_creds
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES
    )
    flow.redirect_uri = 'http://localhost:8080/'
    
    # We call authorization_url to initialize the internal state (including code_verifier)
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print(f"Flow initialized. Internal state set.")
    
    # Now we can use the code provided by the user
    auth_code = "4/0Aci98E85LCzTALe-xh9fyN9gz025RvKH1rUpO6eS4LJhYwF0rvCWwLIL3SYrIcXMe218ig"
    
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
