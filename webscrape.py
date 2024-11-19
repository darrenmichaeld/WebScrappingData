import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import requests  # For API requests
import re


class CoinMarketCapScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920x1080")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def scrape_main_page(self, num_rows=80):
        try:
            # Open the CoinMarketCap main page
            self.driver.get("https://coinmarketcap.com/")
            assert "CoinMarketCap" in self.driver.title
            time.sleep(5)  # Wait for the page to load initially
            
            data = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            # Continue scrolling until enough rows are loaded
            while len(data) < num_rows:
                # Wait for the table to be present
                table = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cmc-table")))
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")  # Locate all loaded rows
                print(f"Rows currently loaded: {len(rows)}")  # Debugging: print the number of rows found

                # Process only new rows
                for row in rows[len(data):]:
                    columns = row.find_elements(By.CSS_SELECTOR, "td")
                    if len(columns) >= 8:  # Ensure enough columns exist
                        name = columns[2].text
                        price = columns[3].text
                        market_cap = columns[7].text
                        volume = columns[8].text
                        data.append({
                            "Name": name, "Price": price, "Market Cap": market_cap, "Volume": volume
                        })
                        if len(data) >= num_rows:  # Stop if the required number of rows is reached
                            break

                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
                time.sleep(5)  # Wait for new data to load
                self.driver.execute_script("window.scrollTo(document.body.scrollHeight / 3, document.body.scrollHeight / 1.5);")
                time.sleep(5)
                self.driver.execute_script("window.scrollTo(document.body.scrollHeight / 1.5, document.body.scrollHeight);")
                time.sleep(5)

                # Check if scrolling reached the end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("No more content to load.")
                    break
                last_height = new_height

            return data

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return []


    def scrape_exchanges(self, num_rows=50):
        try:
            self.driver.get("https://coinmarketcap.com/rankings/exchanges/")
            assert "Top Cryptocurrency Exchanges Ranked By Volume | CoinMarketCap" in self.driver.title

            time.sleep(10)  # Wait for the page to load initially

            data = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            # Continue scrolling until enough rows are loaded
            while len(data) < num_rows:
                # Wait for rows to load
                table = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cmc-table")))
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                print(f"Rows currently loaded: {len(rows)}")  # Debugging: print the number of rows found

                if len(rows) > 0:
                    for row in rows[len(data):]:  # Process only new rows
                        columns = row.find_elements(By.CSS_SELECTOR, "td")
                        if len(columns) >= 6:  # Ensure enough columns exist
                            name = columns[1].text
                            volume = columns[2].text
                            average = columns[3].text
                            weeklyVisit = columns[4].text
                            market = columns[5].text
                            data.append({
                                "Name": name, "Volume": volume, "Average Liquidity": average, 
                                "Weekly Visit": weeklyVisit, "Market": market
                            })
                            if len(data) >= num_rows:  # Stop if the required number of rows is reached
                                break

                # Slowly scroll down to load more data (scroll by smaller increments)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
                time.sleep(10)  # Wait for new data to load
                self.driver.execute_script("window.scrollTo(document.body.scrollHeight / 3, document.body.scrollHeight / 1.5);")
                time.sleep(10)
                self.driver.execute_script("window.scrollTo(document.body.scrollHeight / 1.5, document.body.scrollHeight);")
                time.sleep(10)

                # Check if scrolling reached the end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("No more content to load.")
                    break
                last_height = new_height

            return data

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return []


    def scrape_derivatives(self, num_rows=80):
        try:
            self.driver.get("https://coinmarketcap.com/rankings/exchanges/derivatives/")
            assert "Top Cryptocurrency Derivatives Exchanges Ranked | CoinMarketCap" in self.driver.title, "Title doesn't match"
            
            time.sleep(5)  # Wait for the page to load initially
            
            data = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            # Continue scrolling until enough rows are loaded
            while len(data) < num_rows:
                # Wait for the table to load and get rows
                table = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cmc-table")))
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

                if len(rows) > 0:
                    for row in rows[len(data):]:  # Process only new rows
                        columns = row.find_elements(By.TAG_NAME, "td")
                        
                        # Only process rows with the expected number of columns
                        if len(columns) >= 7:  # Ensure there are at least 7 columns
                            name = columns[1].text
                            volume = columns[2].text
                            makerFees = columns[3].text
                            takerFees = columns[4].text
                            openInterest = columns[5].text
                            marketRank = columns[6].text
                            data.append({
                                "Exchange": name, "Volume": volume, 
                                "Maker Fees": makerFees, "Taker Fees": takerFees, 
                                "Open Interest": openInterest, "Market No.": marketRank
                            })
                            if len(data) >= num_rows:  # Stop if the required number of rows is reached
                                break

                # Slowly scroll down to load more data (scroll by smaller increments)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
                time.sleep(5)  # Wait for new data to load
                self.driver.execute_script("window.scrollTo(document.body.scrollHeight / 3, document.body.scrollHeight / 1.5);")
                time.sleep(5)
                self.driver.execute_script("window.scrollTo(document.body.scrollHeight / 1.5, document.body.scrollHeight);")

                # Check if scrolling reached the end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("No more content to load.")
                    break
                last_height = new_height

            return data

        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error scraping derivatives: {str(e)}")
            return []



    def write_to_csv(self, data, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            print(f"Data written to {filename}")
        except IOError as e:
            print(f"Error writing to CSV: {str(e)}")
    
    def close(self):
        self.driver.quit()
    
    def scrape_specific_crypto(self, search_name):
        """
        Scrape data for a specific cryptocurrency by searching on CoinMarketCap.
        """
        try:
            self.driver.get("https://coinmarketcap.com/")
            
            # Click the search icon
            search_icon = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".Search_mobile-icon-wrapper__u0cEq")))
            search_icon.click()

            # Wait for the input field to appear
            search_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.gNFMEo")))
            search_input.clear()
            search_input.send_keys(search_name)
            time.sleep(5)

            # Wait for suggestions and click the first one
            suggestions = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.SearchCryptoRow_container__QIZ8T")))
            suggestions.click()

            # Wait for the cryptocurrency detail page to load
            crypto = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.coin-stats-header")))

            # Extract Name
            nameResult = crypto.find_elements(By.TAG_NAME, "span")
            cryptoName = nameResult[0].text

            # Extract Price
            price = crypto.find_elements(By.CSS_SELECTOR, "div.czwNaM span.WXGwg")
            cryptoPrice = price[0].text

            allTimeLow = self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div/div[2]/div/div/div[1]/div/div[2]/section/div/div[4]/div[2]/div/div[4]/div/div[2]/span"))).text
            allTimeHigh = self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div/div[2]/div/div/div[1]/div/div[2]/section/div/div[4]/div[2]/div/div[3]/div/div[2]/span"))).text
  
            # Compile data
            data = [{
                "Name": cryptoName, 
                "Price": cryptoPrice, 
                "All Time Low" : allTimeLow,
                "All Time High" : allTimeHigh
            }]
            return data

        except TimeoutException as e:
            print(f"Timeout error: {str(e)}. The website structure may have changed.")
            return []
        except NoSuchElementException as e:
            print(f"Element not found: {str(e)}. Verify selectors.")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return []


def is_valid_fiat_currency(fiat_currency):
    """
    Checks if the provided fiat currency is valid using the CoinGecko API.
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching fiat currency list: {response.status_code}")
            return False
        fiat_list = response.json()
        return fiat_currency.lower() in fiat_list
    except Exception as e:
        print(f"Error checking fiat currency: {str(e)}")
        return False


def convert_currency(crypto_name, quantity, fiat_currency):
    """
    Converts a cryptocurrency amount to a fiat currency value using the CoinGecko API.
    Re-prompts the user if the fiat currency is invalid.
    """
    while not is_valid_fiat_currency(fiat_currency):
        print(f"The fiat currency '{fiat_currency}' is not valid.")
        fiat_currency = input("Please enter a valid fiat currency: ").strip()

    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_name.lower()}&vs_currencies={fiat_currency.lower()}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching data from CoinGecko: {response.status_code}")
            return None
        data = response.json()
        if crypto_name.lower() not in data or fiat_currency.lower() not in data[crypto_name.lower()]:
            print("Invalid cryptocurrency or fiat currency. Please try again.")
            return None
        price = data[crypto_name.lower()][fiat_currency.lower()]
        total_value = price * quantity
        return {"Price_Per_Unit": price, "Total_Value": total_value, "Currency": fiat_currency.lower()}
    except Exception as e:
        print(f"An error occurred during conversion: {str(e)}")
        return None



def get_valid_input(prompt, valid_options):
    """
    Helper function to repeatedly prompt the user until they provide valid input.
    """
    while True:
        user_input = input(prompt).strip().lower()
        if user_input in valid_options:
            return user_input
        print(f"Invalid input. Please choose from {', '.join(valid_options)}.")


def get_positive_float(prompt):
    """
    Helper function to repeatedly prompt for a positive float input.
    """
    while True:
        try:
            value = float(input(prompt))
            if value > 0:
                return value
            else:
                print("Value must be greater than 0.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def main():
    scraper = CoinMarketCapScraper()

    while True:
        print("\nCoinMarketCap Scraper")
        print("1. Scrape Main Page")
        print("2. Scrape Exchanges")
        print("3. Scrape Derivatives")
        print("4. Convert Cryptocurrency to Fiat")
        print("5. Search and Scrap Cryptocurrency")
        print("6. Exit")
        
        choice = get_valid_input("Enter your choice (1-6): ", ["1", "2", "3", "4", "5", "6"])
        
        if choice == '1':
            data = scraper.scrape_main_page()
            if data:
                scraper.write_to_csv(data, "top_cryptocurrencies.csv")
        
        elif choice == '2':
            data = scraper.scrape_exchanges()
            if data:
                scraper.write_to_csv(data, "top_exchanges.csv")
        
        elif choice == '3':
            data = scraper.scrape_derivatives()
            if data:
                scraper.write_to_csv(data, "top_derivatives.csv")
        
        elif choice == '4':
            # Get the cryptocurrency name
            valid_cryptos = ['bitcoin', 'solana', 'ethereum', 'tether', 'doge', 'cardano']
            crypto_name = input(f"Enter the cryptocurrency you want to convert (Choose from {', '.join(valid_cryptos)}): ").strip().lower()

            if crypto_name not in valid_cryptos:
                print("Invalid cryptocurrency. Please choose from the available options.")
                continue
            # Get the quantity
            quantity = get_positive_float(f"Enter the quantity of {crypto_name}: ")

            # Get the fiat currency with dynamic validation
            fiat_currency = input("Enter the fiat currency (e.g., USD, EUR, GBP): ").strip().lower()

            # Perform conversion
            conversion = convert_currency(crypto_name, quantity, fiat_currency)
            if conversion:
                print(f"1 {crypto_name.capitalize()} = {conversion['Price_Per_Unit']} {conversion['Currency']}")
                print(f"Total Value: {conversion['Total_Value']} {conversion['Currency']}")

        elif choice == "5":
            search_name = input("Enter the cryptocurrency name to search: ")
            data = scraper.scrape_specific_crypto(search_name)
            if data:
                filename = f"{search_name}_details.csv"
                scraper.write_to_csv(data, filename)

        elif choice == '6':
            print("Exiting the program...")
            break

    scraper.close()



if __name__ == "__main__":
    main()
