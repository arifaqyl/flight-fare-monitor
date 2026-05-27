import requests

# Test 1: Google Flights
print("Testing Google Flights...")
url1 = "https://www.google.com/travel/flights"
r1 = requests.get(url1)
print(f"Status: {r1.status_code}, Content length: {len(r1.text)}")

# Test 2: Skyscanner
print("\nTesting Skyscanner...")
url2 = "https://www.skyscanner.com.my"
r2 = requests.get(url2)
print(f"Status: {r2.status_code}, Content length: {len(r2.text)}")

print("\nDone. If status = 200, site is accessible.")
