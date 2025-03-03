from Core.Alpacca import Alpacca

if __name__ == '__main__':
    alpacca = Alpacca("phi4", history_location="phi-story.json", frequency_penalty=1, system="Resources/system_prompt.txt")
    print(alpacca.generate("Generate instructions on how to use chat history with the ollama api."))
    print(alpacca.generate("what was my last message?"))
    alpacca.save_history()

