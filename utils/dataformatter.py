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
