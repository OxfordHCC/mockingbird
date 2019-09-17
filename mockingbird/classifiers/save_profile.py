from get_tweets import get_tweets
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os


def main():
    os.system("clear")
    options = Options()
    options.add_experimental_option('detach', True)
    options.add_argument("--disable-infobars")
    # options.add_argument('--kiosk')  # Fills entire screen but doesn't show loading bar or url

    var = input("Please enter your Twitter username here: @")
    print("Gathering Tweets (this may take a few seconds)")
    get_tweets(var, save_csv=True, local=True)

    print("Thanks! Your data has been saved.")

    br = webdriver.Chrome('/Users/adamhare/Google Drive/Oxford/Project/mysite/chromedriver', chrome_options=options)
    br.maximize_window()

    url = 'http://127.0.0.1:8000/twitter/'

    br.get(url)
    form = br.find_element_by_name("username")
    form.send_keys(var)
    form.submit()


if __name__ == '__main__':
    main()
