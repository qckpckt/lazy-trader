from collections import defaultdict
from pprint import pprint

import requests
from requests.exceptions import HTTPError
import yaml

from mail import send_mail


class LazyError(Exception):
    pass


class LazyTrader:
    def __init__(self):

        with open("app/config.yaml", "r") as configfile:
            self.config = yaml.safe_load(configfile)
            self.refresh_token = self.config["auth"]["refresh_token"]
            self.allocation_map = self.config["allocation_map"]

        self.refresh_token_url = "https://login.questrade.com/oauth2/token"
        self.session = requests.Session()
        self._get_credentials()
        self.retries = 3

    def _get_credentials(self):
        params = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        resp = self.session.get(self.refresh_token_url, params=params)
        resp.raise_for_status()
        resp_json = resp.json()
        self.api_server = resp_json.get("api_server")
        self.access_token = resp_json.get("access_token")
        self.refresh_token = resp_json.get("refresh_token")
        print(f"NEW REFRESH TOKEN = {self.refresh_token}")
        pprint(f"NEW REFRESH TOKEN = {self.refresh_token}")

    def _request(self, name: str, path: str, *args, **kwargs):
        """generic request method"""
        method = getattr(self.session, name)
        url = f"{self.api_server}{path}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        for i in range(self.retries):
            try:
                response = method(url, *args, headers=headers, **kwargs)
                if response.status_code == 401:
                    self._get_credentials()
                response.raise_for_status()
                return response.json()
            except HTTPError as e:
                pprint(e)
                continue

    def get(self, path: str):
        return self._request("get", path)

    def _fetch_account_allocations(self, positions: list) -> tuple:
        asset_class_totals = defaultdict(float)
        currency_totals = defaultdict(float)
        for asset_class in self.allocation_map:
            for symbol in self.allocation_map[asset_class]["symbols"]:
                for position in positions:
                    if position["symbol"] == symbol["symbol"]:
                        asset_class_totals[
                            f"{asset_class}_{symbol['currency']}"
                        ] += position["currentMarketValue"]
                        currency_totals[f"{symbol['currency']}"] += position[
                            "currentMarketValue"
                        ]
        return asset_class_totals, currency_totals

    def _calculate_allocation_variances(self, positions: list) -> dict:
        asset_class_totals, currency_totals = self._fetch_account_allocations(positions)
        return {
            k: (
                self.allocation_map[k.split("_CAD")[0]]["allocation"]
                - int(v / currency_totals["CAD"] * 100)
            )
            for (k, v) in asset_class_totals.items()
            if "CAD" in k
        }

    def get_highest_allocation_variance(self, account: dict) -> str:
        positions = self.get(f"v1/accounts/{account['number']}/positions")["positions"]
        variances = self._calculate_allocation_variances(positions)
        highest_variance = sorted(variances.items(), key=lambda item: item[1])[-1][0]
        return {
            "account": account["type"],
            "variances": variances,
            "highest_variance": highest_variance,
            "suggested_buy": self.allocation_map[highest_variance.split("_CAD")[0]][
                "buy"
            ],
        }

    def send_recs(self, trade_recommendations: list):
        recommendation_template = """
            <p style="font-size:14px;font-weight:bold">{account}:</p>
            <p><strong>Highest Variance</strong>: {highest_variance}<br>
            <strong>Suggested Buy</strong>: {suggested_buy}<br>
            </p>
        """
        message_body = f"""
        <html>
            <body>
                <p style="font-size:18px;font-weight:bold">Here are your recommended buys for each account.</p><br><br>
                {'<br>'.join([recommendation_template.format(**i) for i in trade_recommendations])}
            </body>
        </html>
        """
        send_mail(
            self.config["mail"]["source_account"],
            self.config["mail"]["dest_account"],
            "Your purchase recommendations for this week",
            message_body,
        )

    def save_config(self):
        """Store latest refresh token before exiting."""
        self.config["auth"]["refresh_token"] = self.refresh_token
        with open("app/config.yaml", "w") as outfile:
            yaml.safe_dump(self.config, outfile)


def main():
    lt = LazyTrader()
    try:
        accounts = lt.get("v1/accounts")["accounts"]
        trade_recommendations = [
            lt.get_highest_allocation_variance(account) for account in accounts
        ]
        lt.send_recs(trade_recommendations)
    finally:
        lt.save_config()


if __name__ == "__main__":
    main()
