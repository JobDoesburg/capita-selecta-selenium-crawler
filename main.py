import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def parse_args():
    parser = argparse.ArgumentParser(description='The most awesome Selenium Capita Selecta crawler')
    parser.add_argument('-m', help='mobile or desktop')
    parser.add_argument('-u', help='single URL to crawl, this takes precedent over the -i option')
    parser.add_argument('-i', help='path to CSV with domains to crawl')

    args = parser.parse_args()

    if args.m:
        assert args.m == 'mobile' or args.m == 'desktop'

def main():
    args = parse_args()

    driver = webdriver.Chrome()
    driver.get("http://www.python.org")
    assert "Python" in driver.title
    elem = driver.find_element_by_name("q")
    elem.clear()
    elem.send_keys("pycon")
    elem.send_keys(Keys.RETURN)
    assert "No results found." not in driver.page_source
    driver.close()

if __name__ == '__main__':
    main()
