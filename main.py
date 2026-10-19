import functions.greetings as greetings
import functions.scraping as scraping

if __name__ == "__main__":
    greetings.startup()
    try:
        success = scraping.initial_scrap()
    except KeyboardInterrupt:
        print("\nCancelled.")
        success = False
    raise SystemExit(0 if success else 1)
