# My first IB algorithmic trading project

Hi,

welcome to my first algorithmic trading project. There are quite a few points on the ageda for the project.

In a nutshell, I want to design and deploy trading strategies on Interactive Broker's platform. 

The aim is to automate every step of your strategy including, extracting data (stock data and fundamental data), performing technical/fundamental analysis, generating signals, placing trades, risk management etc. 

As a broker at the back of the system, Interactive Brokers will serve me with their Python-wrapped API access.

## Setup

### IB TWS

For getting started you need to get a Interactive Brokers Trading Workstation - abbreviated to IB TWS.

Go to their website and just start a free trail. It wouldn't cost any money. Therefore, no harm spinning up one.

### Install the IB Python Client

Get the latest source code for your machine from here: http://interactivebrokers.github.io/#

Navigate to the downloaded folder. Inside the folder, find the path 'source/pythonclient'. Then, run an install command on the setup.py file. Here is how I have done it in my terminal.

```
cd twsapi_macunix.976.01/IBJts/source/pythonclient
python3 setup.py install
```

### API Configuration Settings

We need to check the option "Enable ActiveX and Socket Clients" in the TWS App. This is required to enable Interactive Brokers Gateway to listen to API calls on a given port.

Note that you need to enter the **correct port number**:
- TWS Live Trading: 7496
- TWS Paper Trading: 7497
- IB Gateway Live Trading: 4001
- IB Gateway Paper Trading: 4002

Also, check "Read only API" if you want to avoid to place/modify trades accidentily (not relevant for paper tarding).

Optinal: Set the Master API Client ID to any given nummer.

## Understanding the IB API Python Wrapper

Find a thorough docs page here: http://interactivebrokers.github.io/tws-api/

All your the source code of the API Wrapper is stored in the aboev mentioned 'source/pythonclient' folder. Navigate to 'ibapi' from there.