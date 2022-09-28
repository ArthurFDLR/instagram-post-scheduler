import json
import requests
from datetime import datetime, timedelta


class GraphAPI:
    def __init__(self, paramaters) -> None: 
        # assert check_GraphAPIParameters(paramaters), "Error in GraphAPI parameters format."

        self.enpoint_base = paramaters['graph_domain'] + '/' + paramaters['graph_version'] + '/'
        self.instagram_account_id = paramaters["instagram_account_id"]
        
        self.access_token = paramaters['access_token']
        self.expiration_date = datetime.fromtimestamp(0)
        assert self.check_token(), "Error in token."
    
    def check_token(self):
        request_access_token = requests.get(
            url = self.enpoint_base + 'debug_token',
            params = {
                "access_token": self.access_token,
                "input_token": self.access_token,
            }
        )
        request_access_token_data = json.loads(request_access_token.content)
        # print(json.dumps(request_access_token_data, indent=2))
        access_token_error = request_access_token_data.get("error", None)

        if access_token_error is not None:
            print(access_token_error)
            return False

        access_token_data = request_access_token_data.get("data", None)

        if access_token_data is None:
            return False
        if not access_token_data.get("is_valid", False):
            print("Token not valid")
            return False
        
        if not set(access_token_data.get("scopes", [])) >= set(("instagram_basic", "instagram_content_publish", "public_profile")):
            print("Missing authorizations")
            return False

        self.expiration_date = datetime.fromtimestamp(access_token_data['expires_at'])
        return True
    
    def get_new_token(self, token:str, client_id:str, client_secret:str):
        update_token_data = requests.get(
            url = self.enpoint_base + 'oauth/access_token',
            params = {
                "grant_type": "fb_exchange_token",
                "fb_exchange_token": token,
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        access_token_data = json.loads(update_token_data.content)
        # print(json.dumps(access_token_data, indent=2))

        return access_token_data.get("access_token")
    
    def post(self, image_url:str, caption:str):
        # Create container
        request_container = requests.post(
            url = self.enpoint_base + self.instagram_account_id + '/media',
            data = {
                'image_url': image_url,
                'caption': caption,
                'access_token': self.access_token,
            }
        )

        request_container_data = json.loads(request_container.content)
        # print(json.dumps(request_container_data, indent=2))
        container_id = request_container_data.get("id", None)

        if container_id is None:
            return False, request_container_data, None

        # Publish content
        publication_container = requests.post(
            url = self.enpoint_base + self.instagram_account_id + '/media_publish',
            data = {
                'creation_id': container_id,
                'access_token': self.access_token,
            }
        )
        request_publication_data = json.loads(publication_container.content)
        # print(json.dumps(request_publication_data, indent=2))

        if "id" not in request_publication_data:
            return False, request_container_data, request_publication_data
        
        return True, request_container_data, request_publication_data
        
if __name__ == "__main__":
    with open('./params.json', 'r') as f:
        param = json.load(f)

    try:
        api = GraphAPI(param)
    except Exception as e:
        print(e)
        exit()
    if api.expiration_date - datetime.now() < timedelta(days=10):
        print(f"WARNING: access_token expires on {api.expiration_date}")
