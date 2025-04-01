import requests

def get_latest_chrome_version():
    url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        stable_version = data['channels']['Stable']['version']
        return stable_version
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")

latest_version = get_latest_chrome_version()
print(f"The latest stable version of Google Chrome is: {latest_version}")
