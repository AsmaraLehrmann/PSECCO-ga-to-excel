import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

URL = "https://bsky.app/profile/polarsecco.bsky.social"

def fetch_followers(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    followers_span = soup.find("span", string=lambda t: "followers" in t.lower() if t else False)
    
    if followers_span:
        followers = followers_span.previous_element.strip()
        followers = followers.replace(',', '')
        return int(followers)
    else:
        raise ValueError("Could not find follower count on page.")

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    followers_count = fetch_followers(URL)

    file_path = os.path.join("data", "follower_counts.csv")

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=["Date", "Followers"])

    df = pd.concat([df, pd.DataFrame([{"Date": today, "Followers": followers_count}])], ignore_index=True)
    df.to_csv(file_path, index=False)

    print(f"Date: {today}, Followers: {followers_count}")
