import re
from datetime import datetime


class DataFormatter:

    @staticmethod
    def clean_data(data_str: str) -> str:
        """Clean a string by removing newline characters and leading/trailing whitespace.
        Args:
            data_str (str): The string to clean.
        Returns:
            str: The cleaned string.
        """
        return data_str.replace("\n", "").strip()

    @staticmethod
    def clean_price_and_currency(data_str: str) -> (str, int):
        """Extract the price and currency from a string.
        Args:
            data_str (str): The string to clean in format [CURRENCY] [PRICE], E.g. USD 1.000
        Returns:
            currency (str): The currency string.
            price (str): The cleaned price string.
        """
        currency, price = data_str.split(" ", 1)
        price = int(price.replace(".", ""))
        return currency, price

    @staticmethod
    def extract_int_value(data_str: str) -> int:
        """Extract an integer value from a string containing currency formatted text.

        Args:
            data_str (str): The string containing the currency value.

        Returns:
            int: The extracted integer value, or None if no value is found.
        """
        # Regular expression pattern to match the amount in the format of $xx.xxx
        match = re.search(r'(?:\$\s*)?(\d+(?:\.\d+)?)', data_str)
        if match:
            amount = int(match.group(1).replace('.', ''))
            return amount
        return 0

    @staticmethod
    def clean_age_data(age):
        current_year = datetime.now().year
        if isinstance(age, (int, float)):
            if 0 < age <= 1000:
                return age
            elif 1000 < age < 10000:
                return current_year - age
        print("Invalid Age Value")
        return 0
