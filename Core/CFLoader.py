class CFLoader:
    initialized: bool = False

    @staticmethod
    def __init__(self):
        if self.initialized:
            print("CFLoader already initialized")
            return
        self.initialized = True
        print("CFLoader initialized")