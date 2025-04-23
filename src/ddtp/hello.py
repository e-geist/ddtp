# Import WebSocket client library
from websocket import create_connection


def main():
    # Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
    ws = create_connection("wss://demo-futures.kraken.com/v2")
    ws.send(
        '''{"method":"subscribe", "params" : 
{
"channel": "level3", 
"symbol": ["XBT/USD","XRP/USD"], 
"token": "",
},
}'''
    )
    # Infinite loop waiting for WebSocket data
    while True:
        print(ws.recv())


if __name__ == "__main__":
    main()
