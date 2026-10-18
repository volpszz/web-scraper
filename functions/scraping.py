import requests


def fetch_page(url):
    try:
        response = requests.get(url, timeout=10)
        return response
    except requests.exceptions.RequestException as error:
        print(f"Erro ao acessar a página: {error}")
        return None


def show_response(response):
    print("Status:", response.status_code)
    print("Content type:", response.headers.get("Content-Type"))
    print("Body preview:")
    print(response.text[:500])


def initial_scrap():
    while True:
        url = input("Insert the target url: ")

        if url.startswith(("http://", "https://")):
            break

        print("Error: URL needs to start with http or https.")

    response = fetch_page(url)

    if response is not None:
        show_response(response)