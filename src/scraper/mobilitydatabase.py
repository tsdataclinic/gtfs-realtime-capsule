import requests


def get_access_token(base_url: str, refresh_token: str):
    result = requests.post(f"{base_url}/tokens",
                           json={"refresh_token": refresh_token})
    result.raise_for_status()
    return result.json()["access_token"]


def get_feed_json(base_url: str, feed_id: str, access_token: str):
    bear_token = {"Authorization": f"Bearer {access_token}"}
    result = requests.get(f"{base_url}/feeds/{feed_id}", headers=bear_token)
    result.raise_for_status()
    return result.json()
