from typing import List

import ollama
from ollama import *

from Core.Logger import Logger
from Core.Priority import Priority
from Utils.FileLoader import load_from_file, load_json, save_json


def separate_thoughts(string: str) -> dict[str, str]:
    """
    Separates the response from the <think>...</think> content
    :param string: The string to separate
    :return: A dictionary with the response and the think content
    """
    if string.find("</think>") != -1:
        thoughts = string.split("</think>")
        return {
            "response": thoughts[0].replace("<think>", "").replace("</think>", "").strip(),
            "think": thoughts[1]
        }
    else:
        return {
            "response": string,
            "think": ""
        }

class ChatExchange:
    user: str
    thoughts: str
    answer: str

    def __init__(self, user: str, thoughts: str, answer: str):
        self.user = user
        self.thoughts = thoughts
        self.answer = answer

    def dict(self) -> dict:
        return {
            "user": self.user,
            "thoughts": self.thoughts,
            "answer": self.answer
        }

def chat_exchange_from_dict(d: dict) -> ChatExchange:
    return ChatExchange(d["user"], d["thoughts"], d["answer"])

def history_string(history: List[ChatExchange]) -> str:
    full = "Chat history:\n"
    is_first = True
    for d in history:
        if is_first:
            is_first = False
            partial = ""
        else:
            partial = f" --Next Message-- \n"
        partial += f"user prompted: '{d.user}'\n"
        partial += f"you thought: '{d.thoughts}'\n"
        partial += f"you answered: '{d.answer}'\n"
        full += partial
    return full

class Alpacca:
    history: List[ChatExchange] # History of messages and responses between the user and the model
    history_location: str # The location of the history file
    context: [[int]] = [] # The context of the conversation

    def __init__(self, model: str, previous_history: [ChatExchange] = None, temperature: float = 1, frequency_penalty: float = 0, stop: [str] = None, system: str = None, history_location: str = None):
        self.model = model # The model to use
        self.history = previous_history
        self.history_location = history_location
        self.client = Client()
        self.stop = stop
        self.options = {"temperature": temperature, "frequency_penalty": frequency_penalty, "stop": stop}
        if system:
            self.system_prompt = load_from_file(system)
            self.use_system = True
        else:
            self.use_system = False

        if history_location or previous_history:
            self.history = [chat_exchange_from_dict(d) for d in load_json(history_location, create=True)]
            self.use_history = True
        else:
            self.use_history = False

    def __str__(self):
        return f"Alpacca model of: {self.model}"

    def generate(self, prompt) -> ChatResponse:
        """
        Generate a response from the model based on the prompt, system prompt and provided history
        :param prompt: The prompt to generate a response from
        :return: The response from the model
        """
        Logger.log(f"Generating Response using Alpacca model: {self.model}", Priority.NORMAL)
        user_question = prompt
        context = self.use_history and history_string(self.history) or ""
        system_prompt = self.use_system and self.system_prompt or ""
        prompt += f"\n{context}"
        Logger.log(f"Prompt: {prompt}", Priority.DEBUG)
        response: ChatResponse = self.client.generate(model=self.model, options=self.options, prompt=prompt, system=system_prompt)
        self.context.append(response)
        print(response.context)

        lama_response = separate_thoughts(response["response"])
        print(lama_response)
        if self.use_history: self.history.append(ChatExchange(user_question, lama_response["think"], lama_response["response"]))
        return response

    def save_history(self):
        """
        Save the history to a file
        """
        if self.use_history:
            Logger.log(f"Alpacca: Saving history to: {self.history_location}", Priority.NORMAL)
            save_json([h.dict() for h in self.history], self.history_location)
            Logger.log("History saved", Priority.NORMAL)
        else:
            Logger.log("History is not enabled", Priority.CRITICAL)
            raise Exception("History is not enabled")

    async def generate_async(self, prompt):
        Logger.log(f"Generating Async Response using Alpacca model: {self.model}", Priority.NORMAL)
        user_question = prompt
        context = self.use_history and history_string(self.history) or ""
        system_prompt = self.use_system and self.system_prompt or ""
        prompt += f"\n{context}"
        Logger.log(f"Prompt: {prompt}", Priority.DEBUG)
        iterator = await ollama.AsyncClient().generate(model=self.model, options=self.options, prompt=prompt, system=system_prompt, stream=True)
        return iterator
