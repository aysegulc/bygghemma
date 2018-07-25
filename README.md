
Bygghemma Scraping Project
-------------------------

This scrapy project is built to extract detailed product info from Bygghemma.se.

Spider makes a request to an json endpoint for a single category and parses the json data to scrape product information.

The spider needs to be extended to scrape the entire store.


```bash
# Save items to csv file
scrapy crawl bygghemma -o bygghemma_product_data.csv
# save items to json file
scrapy crawl bygghemma -o bygghemma_product_data.json
```
