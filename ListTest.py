import ollama

if __name__ == "__main__":
    list = ollama.list().models

    for model in list:
        #print(model)
        print(ollama.Client().show(model["model"]).modelinfo)
        print(ollama.Client().show(model["model"]).modelinfo.keys())
        try:
            print(ollama.Client().show(model["model"]).modelinfo["general.type"])
        except KeyError:
            print("No general.type")