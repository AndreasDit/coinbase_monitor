# coinbase monitor
This Package creates the data basis for my Altcoin Monitor on Coinbase.

# Setup and install ODBC Driver for Microsoft SQL Server 17
Install here: https://learn.microsoft.com/th-th/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-2017

Perform following commands:
sudo ln -s /opt/homebrew/etc/odbcinst.ini /etc/odbcinst.ini
sudo ln -s /opt/homebrew/etc/odbc.ini /etc/odbc.ini

## Hosting services

Services I tried:
- Kamatera: https://console.kamatera.com. small server with docker installed. super simple and cheap.

## Docker
1. Pull docker image: adtest123/hate_on_twitter
2. docker run -d -it image
3. docker exec -it containername /bin/bash
4. /etc/init.d/cron restart
