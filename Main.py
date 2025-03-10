from Core.Alpacca import Alpacca
from Core.Console import *

if __name__ == '__main__':
    alpacca = Alpacca("llama3.1:8b-instruct-q8_0", history_location="phi-story.json", frequency_penalty=0.5, system="Resources/system_prompt.txt")

    # print(alpacca.generate("Write a short inspirational story!"))
    for parts in alpacca.generate_iterable("Hello World!"):
        print(parts["response"])

    alpacca.save_history()