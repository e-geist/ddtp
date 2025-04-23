"""
REST implementation for Kraken Derivatives.
Taken from: https://github.com/CryptoFacilities/REST-v3-Python/blob/master/cfRestApiV3.py
and adapted.
"""
# Crypto Facilities Ltd REST API v3

# Copyright (c) 2018 Crypto Facilities

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import time
import base64
import hashlib
import hmac
import json
import urllib.request as urllib2
import urllib.parse as urllib
import ssl


class KrakenDerivREST(object):
    def __init__(
        self,
        api_path,
        api_public_key="",
        api_private_key="",
        timeout=10,
        check_certificate=True,
        use_nonce=False,
    ):
        self.api_path = api_path
        self.api_public_key = api_public_key
        self.api_private_key = api_private_key
        self.timeout = timeout
        self.nonce = 0
        self.check_certificate = check_certificate
        self.use_nonce = use_nonce

    ##### public endpoints #####

    # returns all instruments with specifications
    def get_instruments(self):
        endpoint = "/derivatives/api/v3/instruments"
        return self.make_request("GET", endpoint)

    # returns market data for all instruments
    def get_tickers(self):
        endpoint = "/derivatives/api/v3/tickers"
        return self.make_request("GET", endpoint)

    # returns the entire order book of a futures
    def get_orderbook(self, symbol):
        endpoint = "/derivatives/api/v3/orderbook"
        postUrl = "symbol=%s" % symbol
        return self.make_request("GET", endpoint, post_url=postUrl)

    # returns historical data for futures and indices
    def get_history(self, symbol, lastTime=""):
        endpoint = "/derivatives/api/v3/history"
        if lastTime != "":
            postUrl = "symbol=%s&lastTime=%s" % (symbol, lastTime)
        else:
            postUrl = "symbol=%s" % symbol
        return self.make_request("GET", endpoint, post_url=postUrl)

    ##### private endpoints #####

    # returns key account information
    # Deprecated because it returns info about the Futures margin account
    # Use get_accounts instead
    def get_account(self):
        endpoint = "/derivatives/api/v3/account"
        return self.make_request("GET", endpoint)

    # returns key account information
    def get_accounts(self):
        endpoint = "/derivatives/api/v3/accounts"
        return self.make_request("GET", endpoint)

    # places an order
    def send_order(
        self,
        order_type,
        symbol,
        side,
        size,
        limit_price,
        stop_price=None,
        client_order_id=None,
    ):
        endpoint = "/derivatives/api/v3/sendorder"
        postBody = "orderType=%s&symbol=%s&side=%s&size=%s&limitPrice=%s" % (
            order_type,
            symbol,
            side,
            size,
            limit_price,
        )

        if order_type == "stp" and stop_price is not None:
            postBody += "&stopPrice=%s" % stop_price

        if client_order_id is not None:
            postBody += "&cliOrdId=%s" % client_order_id

        return self.make_request("POST", endpoint, post_body=postBody)

    # places an order
    def send_order_1(self, order):
        endpoint = "/derivatives/api/v3/sendorder"
        postBody = urllib.urlencode(order)
        return self.make_request("POST", endpoint, post_body=postBody)

    # edit an order
    def edit_order(self, edit):
        endpoint = "/derivatives/api/v3/editorder"
        postBody = urllib.urlencode(edit)
        return self.make_request("POST", endpoint, post_body=postBody)

    # cancels an order
    def cancel_order(self, order_id=None, cli_ord_id=None):
        endpoint = "/derivatives/api/v3/cancelorder"

        if order_id is None:
            postBody = "cliOrdId=%s" % cli_ord_id
        else:
            postBody = "order_id=%s" % order_id

        return self.make_request("POST", endpoint, post_body=postBody)

    # cancel all orders
    def cancel_all_orders(self, symbol=None):
        endpoint = "/derivatives/api/v3/cancelallorders"
        if symbol is not None:
            postbody = "symbol=%s" % symbol
        else:
            postbody = ""

        return self.make_request("POST", endpoint, post_body=postbody)

    # cancel all orders after
    def cancel_all_orders_after(self, timeout_in_seconds=60):
        endpoint = "/derivatives/api/v3/cancelallordersafter"
        postbody = "timeout=%s" % timeout_in_seconds

        return self.make_request("POST", endpoint, post_body=postbody)

    # places or cancels orders in batch
    def send_batchorder(self, json_element):
        endpoint = "/derivatives/api/v3/batchorder"
        postBody = "json=%s" % json_element
        return self.make_request("POST", endpoint, post_body=postBody)

    # returns all open orders
    def get_open_orders(self):
        endpoint = "/derivatives/api/v3/openorders"
        return self.make_request("GET", endpoint)

    # returns filled orders
    def get_fills(self, lastFillTime=""):
        endpoint = "/derivatives/api/v3/fills"
        if lastFillTime != "":
            postUrl = "lastFillTime=%s" % lastFillTime
        else:
            postUrl = ""
        return self.make_request("GET", endpoint, post_url=postUrl)

    # returns all open positions
    def get_open_positions(self):
        endpoint = "/derivatives/api/v3/openpositions"
        return self.make_request("GET", endpoint)

    # sends an xbt withdrawal request
    def send_withdrawal(self, targetAddress, currency, amount):
        endpoint = "/derivatives/api/v3/withdrawal"
        postBody = "targetAddress=%s&currency=%s&amount=%s" % (
            targetAddress,
            currency,
            amount,
        )
        return self.make_request("POST", endpoint, post_body=postBody)

    # returns xbt transfers
    def get_transfers(self, lastTransferTime=""):
        endpoint = "/derivatives/api/v3/transfers"
        if lastTransferTime != "":
            postUrl = "lastTransferTime=%s" % lastTransferTime
        else:
            postUrl = ""
        return self.make_request("GET", endpoint, post_url=postUrl)

    # returns all notifications
    def get_notifications(self):
        endpoint = "/derivatives/api/v3/notifications"
        return self.make_request("GET", endpoint)

    # makes an internal transfer
    def transfer(self, fromAccount, toAccount, unit, amount):
        endpoint = "/derivatives/api/v3/transfer"
        postBody = "fromAccount=%s&toAccount=%s&unit=%s&amount=%s" % (
            fromAccount,
            toAccount,
            unit,
            amount,
        )
        return self.make_request("POST", endpoint, post_body=postBody)

    # accountlog csv
    def get_accountlog(self):
        endpoint = "/api/history/v2/accountlogcsv"
        return self.make_request("GET", endpoint)

    def _get_partial_historical_elements(self, elementType, **params):
        endpoint = "/api/history/v2/%s" % elementType

        params = {k: v for k, v in params.items() if v is not None}
        postUrl = urllib.urlencode(params)

        return self.make_request_raw("GET", endpoint, postUrl)

    def _get_historical_elements(
        self, elementType, since=None, before=None, sort=None, limit=1000
    ):
        elements = []

        continuationToken = None

        while True:
            res = self._get_partial_historical_elements(
                elementType,
                since=since,
                before=before,
                sort=sort,
                continuationToken=continuationToken,
            )
            body = json.loads(res.read().decode("utf-8"))
            elements = elements + body["elements"]

            if (
                res.headers["is-truncated"] is None
                or res.headers["is-truncated"] == "false"
            ):
                continuationToken = None
                break
            else:
                continuationToken = res.headers["next-continuation-token"]

            if len(elements) >= limit:
                elements = elements[:limit]
                break

        return elements

    def get_orders(self, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves orders of your account. With default parameters it gets the 1000 newest orders.

        :param since: Timestamp in milliseconds. Retrieves orders starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves orders before this time.
        :param sort: String "asc" or "desc". The sorting of orders.
        :param limit: Amount of orders to be retrieved.
        :return: List of orders
        """

        return self._get_historical_elements("orders", since, before, sort, limit)

    def get_executions(self, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves executions of your account. With default parameters it gets the 1000 newest executions.

        :param since: Timestamp in milliseconds. Retrieves executions starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves executions before this time.
        :param sort: String "asc" or "desc". The sorting of executions.
        :param limit: Amount of executions to be retrieved.
        :return: List of executions
        """

        return self._get_historical_elements("executions", since, before, sort, limit)

    def get_market_price(self, symbol, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves prices of given symbol. With default parameters it gets the 1000 newest prices.

        :param symbol: Name of a symbol. For example "PI_XBTUSD".
        :param since: Timestamp in milliseconds. Retrieves prices starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves prices before this time.
        :param sort: String "asc" or "desc". The sorting of prices.
        :param limit: Amount of prices to be retrieved.
        :return: List of prices
        """

        return self._get_historical_elements(
            "market/" + symbol + "/price", since, before, sort, limit
        )

    def get_market_orders(self, symbol, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves orders of given symbol. With default parameters it gets the 1000 newest orders.

        :param symbol: Name of a symbol. For example "PI_XBTUSD".
        :param since: Timestamp in milliseconds. Retrieves orders starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves orders before this time.
        :param sort: String "asc" or "desc". The sorting of orders.
        :param limit: Amount of orders to be retrieved.
        :return: List of orders
        """

        return self._get_historical_elements(
            "market/" + symbol + "/orders", since, before, sort, limit
        )

    def get_market_executions(
        self, symbol, since=None, before=None, sort=None, limit=1000
    ):
        """
        Retrieves executions of given symbol. With default parameters it gets the 1000 newest executions.

        :param symbol: Name of a symbol. For example "PI_XBTUSD".
        :param since: Timestamp in milliseconds. Retrieves executions starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves executions before this time.
        :param sort: String "asc" or "desc". The sorting of executions.
        :param limit: Amount of executions to be retrieved.
        :return: List of executions
        """

        return self._get_historical_elements(
            "market/" + symbol + "/executions", since, before, sort, limit
        )

    # signs a message
    def sign_message(self, endpoint, postData, nonce=""):
        if endpoint.startswith("/derivatives"):
            endpoint = endpoint[len("/derivatives") :]

        # step 1: concatenate postData, nonce + endpoint
        message = postData + nonce + endpoint

        # step 2: hash the result of step 1 with SHA256
        sha256_hash = hashlib.sha256()
        sha256_hash.update(message.encode("utf8"))
        hash_digest = sha256_hash.digest()

        # step 3: base64 decode apiPrivateKey
        secretDecoded = base64.b64decode(self.api_private_key)

        # step 4: use result of step 3 to has the result of step 2 with HMAC-SHA512
        hmac_digest = hmac.new(secretDecoded, hash_digest, hashlib.sha512).digest()

        # step 5: base64 encode the result of step 4 and return
        return base64.b64encode(hmac_digest)

    # creates a unique nonce
    def get_nonce(self):
        # https://en.wikipedia.org/wiki/Modulo_operation
        self.nonce = (self.nonce + 1) & 8191
        return str(int(time.time() * 1000)) + str(self.nonce).zfill(4)

    # sends an HTTP request
    def make_request_raw(self, request_type, endpoint, post_url="", post_body=""):
        # create authentication headers
        postData = post_url + post_body

        if self.use_nonce:
            nonce = self.get_nonce()
            signature = self.sign_message(endpoint, postData, nonce=nonce)
            authentHeaders = {
                "APIKey": self.api_public_key,
                "Nonce": nonce,
                "Authent": signature,
            }
        else:
            signature = self.sign_message(endpoint, postData)
            authentHeaders = {"APIKey": self.api_public_key, "Authent": signature}

        authentHeaders["User-Agent"] = "cf-api-python/1.0"

        # create request
        if post_url != "":
            url = self.api_path + endpoint + "?" + post_url
        else:
            url = self.api_path + endpoint

        request = urllib2.Request(url, str.encode(post_body), authentHeaders)
        request.get_method = lambda: request_type

        # read response
        if self.check_certificate:
            response = urllib2.urlopen(request, timeout=self.timeout)
        else:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            response = urllib2.urlopen(request, context=ctx, timeout=self.timeout)

        # return
        return response

    # sends an HTTP request and read response body
    def make_request(self, request_type, endpoint, post_url="", post_body=""):
        return (
            self.make_request_raw(request_type, endpoint, post_url, post_body)
            .read()
            .decode("utf-8")
        )
