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
        """
        Clean and convert age data to integer.
        Returns the number of years of the property.
        Returns 0 for new properties ("A estrenar").
        Returns None if age cannot be determined.
        """
        if not age:
            return None

        age = str(age).lower().strip()

        # Handle "A estrenar" case
        if "estrenar" in age:
            return 0

        # Try to extract year if it's a year format
        try:
            # If it's a year (e.g., "1990")
            if len(age) == 4 and age.isdigit():
                year = int(age)
                current_year = datetime.now().year
                return current_year - year

            # If it contains "años" or similar
            if "año" in age or "años" in age:
                # Extract numbers from string
                numbers = ''.join(filter(str.isdigit, age))
                if numbers:
                    return int(numbers)

            # If it's just a number
            if age.isdigit():
                return int(age)

        except (ValueError, TypeError):
            pass

        return None
