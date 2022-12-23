#!/bin/sh
sudo pkill -f "python"
sudo /opt/miniconda/bin/python3.7 /hate_on_twitter/src/crawler/crawl_hashtags.py
sudo /opt/miniconda/bin/python3.7 /hate_on_twitter/src/main.py
# sudo /opt/miniconda/bin/python3.7 /hate_on_twitter/src/main.py
# sudo /opt/miniconda/bin/python3.7 /hate_on_twitter/src/main.py
