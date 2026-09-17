import json
import os
import urllib.request


def provider_a(ip_address: str):
    """
    Provider A: ip-api.com
    """

    # Deterministic test switch
    if os.getenv("DISABLE_GEO_PROVIDER_A", "false").lower() == "true":
        print("Provider A disabled for testing")
        return None

    url = f"http://ip-api.com/json/{ip_address}"

    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode())

        if data.get("status") == "success":
            return {
                "country": data.get("country"),
                "city": data.get("city"),
                "provider": "ip-api"
            }

    except Exception as error:
        print(f"Provider A failed: {error}")

    return None


def provider_b(ip_address: str):
    """
    Provider B: ipapi.co
    """

    # Deterministic test switch
    if os.getenv("DISABLE_GEO_PROVIDER_B", "false").lower() == "true":
        print("Provider B disabled for testing")
        return None

    url = f"https://ipapi.co/{ip_address}/json/"

    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode())

        if not data.get("error"):
            return {
                "country": data.get("country_name"),
                "city": data.get("city"),
                "provider": "ipapi"
            }

    except Exception as error:
        print(f"Provider B failed: {error}")

    return None


def get_geo_data(ip_address: str):
    """
    Fallback chain:

    Provider A
        ↓ failure
    Provider B
        ↓ failure
    Submission continues without geo data.
    """

    # Normally localhost has no useful public geo data.
    # GEO_TEST_IP lets us use a public test IP during local testing.
    test_ip = os.getenv("GEO_TEST_IP")

    if test_ip:
        ip_address = test_ip

    if ip_address in ("127.0.0.1", "::1", "localhost"):
        return {
            "country": None,
            "city": None,
            "provider": None
        }

    geo = provider_a(ip_address)

    if geo:
        return geo

    geo = provider_b(ip_address)

    if geo:
        return geo

    # Both providers failed.
    # Do not fail the lead submission.
    return {
        "country": None,
        "city": None,
        "provider": None
    }