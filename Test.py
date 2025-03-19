from Core.Alpacca import Alpacca, VALID_PARAMETERS

if __name__ == "__main__":
    alpaca = Alpacca("phi4")
    for a in VALID_PARAMETERS:
        # print(f"Testing {a}")
        print(f"Name: {a['name']}, Type: {a['type']}, min: {a['min']}, max: {a['max']}")

    key: str = input("Write a value to modify: ")
    print(f"key: '{key}'")
    value: str = input("Write a value to set: ")
    print(f"value: '{value}', type: {type(value)}")
    # filter VALID_PARAMETERS to get the type corresponding to the key
    parameter: dict = list(filter(lambda x: x["name"] == key, VALID_PARAMETERS))[0]
    print(parameter)
    print(f"To cast to: {parameter['type']}")
    to_cast: type = parameter["type"]
    # cast the value to the type corresponding to the key
    value = to_cast(value)
    print(f"To cast: {value}, type: {type(value)}")
