import pandas as pd

def worker(cls):
    page = 1
    batch = []
    failed_pages = []
    while True:
        response = cls.get(params={'page': page})
        page += 1
        if not cls.validate(response):
            failed_pages.append(page)
            continue
        df_page = pd.DataFrame(response['results'])
        batch.append(df_page)

        if page % 50 == 0:
            cls.logger.info(F"SUCCESS {page} pages")

        if page % cls.pages_per_batch == 0:
            cls.save_batch(batch)
            batch = []
        
        if page >= response.get("total_pages", 1):
            cls.logger.info(f"Reached last page / API page limit: {page} / {response.get("total_pages", 1)}")
            if batch:
                cls.save_batch(batch)
            break
        if cls.total_pages and page >= cls.total_pages:
            cls.logger.info(f"Reached defined page limit: {page} / {cls.total_pages}")
            if batch:
                cls.save_batch(batch)
            break
    
    if failed_pages:
        cls.logger.warning(f"Processing compleate with Failed pages: {failed_pages}")
    else:
        cls.logger.info(f"Processing ALL pages compleated successfully!")