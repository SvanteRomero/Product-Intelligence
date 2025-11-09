# In crawler/product_intelligence/spiders/gsmarena_spider.py

import scrapy
from scrapy_playwright.page import PageMethod
import logging
import redis
import datetime
import csv # Import the CSV library

class GsmarenaSpider(scrapy.Spider):
    name = 'gsmarena'

    def __init__(self, *args, **kwargs):
        super(GsmarenaSpider, self).__init__(*args, **kwargs)
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        # This list will hold all scraped items in memory
        self.scraped_items = []
        logging.info("Spider connected to Redis.")

    async def start(self):
        urls = ['https://www.gsmarena.com/reviews.php3']
        for url in urls:
            yield scrapy.Request(
                url,
                callback=self.parse_list,
                meta={"playwright": True}
            )

    async def parse_list(self, response):
        logging.info(f"Parsing review list page: {response.url}")
        review_items = response.css('div.review-item')
        
        for item in review_items:
            date_str = item.css('span.meta-item-time::text').get()
            if date_str:
                try:
                    review_date = datetime.datetime.strptime(date_str, '%d %B %Y')
                    if review_date.year >= 2022:
                        review_link = item.css('h3.review-item-title a::attr(href)').get()
                        if review_link:
                            yield response.follow(
                                review_link, 
                                callback=self.parse_review,
                                meta={
                                    "playwright": True,
                                    "playwright_page_methods": [
                                        PageMethod("wait_for_selector", "#user-comments"),
                                    ],
                                }
                            )
                except ValueError:
                    logging.warning(f"Could not parse date format for: '{date_str}'.")

        next_page = response.css('a.prevnextbutton[title="Next page"]::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_list, meta={"playwright": True})

    async def parse_review(self, response):
        product_name = response.css('h1.article-info-name::text').get()
        if not product_name:
            logging.warning(f"No product name found on {response.url}")
            return
        
        logging.info(f"Scraping review for: {product_name.strip()}")

        specs_dict = {}
        spec_rows = response.css('ul.article-blurb-findings li')
        for row in spec_rows:
            key = row.css('b::text').get()
            value = ''.join(row.xpath('./text()').getall()).strip()
            if key:
                specs_dict[key.replace(':', '').strip()] = value.strip()
        
        scraped_data = {
            'product_name': product_name.strip(),
            'source': 'gsmarena.com',
            'url': response.url,
            'specifications': specs_dict,
        }

        comments_link = response.css('a:contains("Read all comments")::attr(href)').get()
        if comments_link:
            yield response.follow(
                comments_link, 
                callback=self.parse_comments,
                meta={
                    "playwright": True,
                    "scraped_data": scraped_data,
                    "comments": []
                }
            )
        else:
            scraped_data['user_comments'] = []
            self.scraped_items.append(scraped_data)

    async def parse_comments(self, response):
        scraped_data = response.meta["scraped_data"]
        comments = response.meta["comments"]
        
        new_comments = response.css('p.uopin::text').getall()
        comments.extend([comment.strip() for comment in new_comments])
        
        logging.info(f"Collected {len(new_comments)} comments for '{scraped_data.get('product_name')}'.")

        next_page = response.css('a.pages-next::attr(href)').get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_comments,
                meta={ "playwright": True, "scraped_data": scraped_data, "comments": comments }
            )
        else:
            scraped_data['user_comments'] = comments
            self.scraped_items.append(scraped_data)
            
            product_name = scraped_data.get('product_name')
            if product_name:
                self.redis_client.rpush('product_queue', product_name)
                logging.info(f"SENT '{product_name}' to Redis queue.")

    def closed(self, reason):
        """
        This method is called when the spider finishes its crawl.
        It writes all collected data to a single CSV file.
        """
        logging.info(f"Spider finished: {reason}. Writing {len(self.scraped_items)} items to CSV.")
        
        if not self.scraped_items:
            return

        # Dynamically create the header from all unique spec keys
        header = ['product_name', 'url', 'user_comments']
        all_spec_keys = set()
        for item in self.scraped_items:
            all_spec_keys.update(item.get('specifications', {}).keys())
        
        # Sort spec keys for consistent column order
        sorted_spec_keys = sorted(list(all_spec_keys))
        header.extend(sorted_spec_keys)

        with open('gsmarena_reviews.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()

            for item in self.scraped_items:
                # Flatten the data for the CSV row
                row_data = {
                    'product_name': item.get('product_name'),
                    'url': item.get('url'),
                    # Join all comments into a single string, separated by a newline
                    'user_comments': "\n".join(item.get('user_comments', [])),
                }
                # Add the specification data to the row
                row_data.update(item.get('specifications', {}))
                
                writer.writerow(row_data)
        
        logging.info("Successfully saved data to gsmarena_reviews.csv")