import argparse

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

if __name__ == '__main__':
    main()
