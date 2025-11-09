# In consumer/get_reddit_data.py
import redis
import praw
import csv # Import the CSV library
import os  # Import the OS library to check for file existence
import time
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_reddit_opinions(product_name, reddit_client, subreddit_name="Android", post_limit=5):
    """
    Searches a subreddit for a product name and scrapes comments from the top posts.
    """
    subreddit = reddit_client.subreddit(subreddit_name)
    logging.info(f"Searching for '{product_name}' in r/{subreddit_name}...")

    search_query = f'"{product_name}"'
    search_results = subreddit.search(search_query, sort="relevance", limit=post_limit)

    all_comments = []
    posts_found = 0
    try:
        for post in search_results:
            posts_found += 1
            logging.info(f"--- Scraping comments from post: '{post.title}' ---")
            
            post.comments.replace_more(limit=0)
            
            for comment in post.comments.list():
                # We only care about the comment text now
                all_comments.append(comment.body)

    except Exception as e:
        logging.error(f"Could not process posts for '{product_name}': {e}")
        return None

    if posts_found == 0:
        logging.warning(f"⚠️ No Reddit posts found for '{product_name}'.")
    
    logging.info(f"✅ Found a total of {len(all_comments)} comments for '{product_name}'.")
    return all_comments

def consume_products():
    """
    Connects to Redis and processes product names from the queue, appending to a single CSV.
    """
    redis_client = redis.Redis(host='redis', port=6379, db=0)
    output_filename = "reddit_opinions.csv"
    
    # Check if the file exists to decide whether to write the header
    file_exists = os.path.isfile(output_filename)

    # Open the file in append mode ('a')
    with open(output_filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # If the file is new, write the header row
        if not file_exists:
            writer.writerow(["product_name", "comment_text"])
            logging.info(f"Created new output file: {output_filename}")

        logging.info("▶️ Reddit Consumer waiting for products from the queue...")

        try:
            reddit = praw.Reddit("bot1")
            logging.info(f"✅ Successfully connected to Reddit as user: {reddit.user.me()}")
        except Exception as e:
            logging.error(f"❌ Could not connect to Reddit. Check praw.ini. Error: {e}")
            return

        while True:
            try:
                # Wait for a message from the 'product_queue'
                _, product_name_bytes = redis_client.blpop('product_queue')
                product_name = product_name_bytes.decode('utf-8')
                
                logging.info(f"RECEIVED product from queue: '{product_name}'")
                
                comments = fetch_reddit_opinions(product_name, reddit_client=reddit)
                
                if comments:
                    for comment in comments:
                        # Write each comment as a new row in the CSV
                        writer.writerow([product_name, comment])
                    # Ensure data is written to disk immediately
                    f.flush()
                    logging.info(f"✅ Appended {len(comments)} comments for '{product_name}' to {output_filename}")

            except Exception as e:
                logging.error(f"An error occurred in the main loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    consume_products()