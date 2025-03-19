import math
import typing
from typing import List, Iterator, Any

import ollama
import requests
from ollama import *
from requests import request, RequestException

from Core.Logger import Logger
from Core.Priority import Priority
from Utils.FileLoader import load_from_file, load_json, save_json


VALID_PARAMETERS = [
    {"name": "temperature", "type": float, "min": 0, "max": 2, "default": 0.8,
     "description": "Controls the randomness of the model. Lower values make the model more deterministic."},
    {"name": "frequency_penalty", "type": float, "min": 0, "max": 2, "default": 0.0,
     "description": "Controls the length of the response. Lower values make the model more verbose."},
    #{"name": "stop", "type": list[str],
    # "description": "A list of strings that the model will stop generating at."},
    {"name": "num_ctx", "type": int, "min": 2048, "max": math.inf, "default": 4096,
     "description": "The number of context messages to use."},
    {"name": "repeat_penalty", "type": float, "min": 0, "max": 2, "default": 1.1,
     "description": "Controls the repetition of the model. Lower values make the model less repetitive. Disabled if repeat_last_n is -1."},
    {"name": "repeat_last_n", "type": int, "min": -1, "max": math.inf, "default": 64,
     "description": "Controls the window size to check for repetition. -1 disables repeat_penalty."},
    {"name": "num_predict", "type": int, "min": -2, "max": math.inf, "default": 128, # -2 fills the context window and -1 means no limit
     "description": "The maximum number of tokens to predict. -1 means no limit. -2 fills the context window."},
    {"name": "top_k", "type": int, "min": 1, "max": 100, "default": 40,
     "description": "A lower value makes the model more conservative in it's answers."},
    {"name": "top_p", "type": float, "min": 0, "max": 1, "default": 0.9,
     "description": "A lower value makes the model more conservative in it's answers."},
]

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

class RemoteException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message

class Alpacca:
    _history: List[ChatExchange] # History of messages and responses between the user and the model
    _history_location: str # The location of the history file
    context: [[int]] = [] # The context of the conversation
    _remote: str = None
    _use_remote: bool = False # If the model is remote
    _options: dict = {}

    def __init__(self, model: str, previous_history: [ChatExchange] = None, system: str = None, history_location: str = None, identifier: str = None, host: str = None, options: dict = None, **kwargs):
        self._model = model # The model to use
        self._history = previous_history
        self._history_location = history_location
        self.identifier = identifier
        self._client = Client()
        if host is not None:
            self._client = Client(host=host)
            self._remote = host
            self._use_remote = True
            if not self.check_connection():
                raise RemoteException(f"Connection failed for remote: {host}! Please check the connection and try again.")

        if options is not None:
            self._options.update(options)

        for key, value in kwargs.items():
            self.set_option(key, value)

        if system is not None:
            self._system_prompt_location = system
            self._system_prompt = load_from_file(system)
            self._use_system = True
        else:
            self._use_system = False

        if history_location or previous_history:
            try:
                self._history = [chat_exchange_from_dict(d) for d in load_json(history_location, create=True)]
            except FileNotFoundError:
                self._history = []
            self._use_history = True
        else:
            self._use_history = False

    def __str__(self):
        return f"Alpacca model of: {self._model}"

    def check_connection(self) -> bool:
        """
        Check if the connection to a remote host is successful
        :return: True if the connection is successful
        """
        try:
            if self._use_remote:
                response = requests.get(f"http://{self._remote}", timeout=5)
                Logger.log(f"Response: {response}", Priority.NORMAL)
                Logger.log(f"Response: {response.text}", Priority.NORMAL)
            else:
                response = requests.get("0.0.0.0:11434", timeout=5)
        except Exception as e:
            Logger.log(f"Exception: {e}", Priority.NORMAL)
            return False
        return response.text.strip().upper() == "OLLAMA IS RUNNING"

    def generate(self, prompt) -> ChatResponse:
        """
        Generate a response from the model based on the prompt, system prompt and provided history
        :param prompt: The prompt to generate a response from
        :return: The response from the model
        """
        Logger.log(f"Generating Response Response using Alpacca model: {self._model}", Priority.NORMAL)
        user_question = prompt
        prompt = self._make_prompt(prompt)
        Logger.log(f"Prompt: {prompt}", Priority.DEBUG)
        response: ChatResponse = self._client.generate(model=self._model, options=self._options, prompt=prompt)
        self.context.append(response)
        print(response.context)

        lama_response = separate_thoughts(response["response"])
        print(lama_response)
        if self._use_history: self._history.append(ChatExchange(user_question, lama_response["think"], lama_response["response"]))
        return response

    def save_history(self) -> None:
        """
        Save the history to a file
        """
        if self._use_history:
            Logger.log(f"Alpacca: Saving history to: {self._history_location}", Priority.NORMAL)
            save_json([h.dict() for h in self._history], self._history_location)
            Logger.log("History saved", Priority.NORMAL)
        else:
            Logger.log("History is not enabled", Priority.CRITICAL)
            raise Exception("History is not enabled")

    def save_alpacca_settings(self, location: str):
        """
        Save the settings of the model to a file
        :param location: The location to save the settings to
        """
        Logger.log(f"Alpacca: Saving settings to: {location}", Priority.NORMAL)
        save_json(self.settings_to_dict(), location)
        Logger.log("Settings saved", Priority.NORMAL)

    def settings_to_dict(self) -> dict:
        """
        Get the settings of the model as a dictionary
        :return: The settings of the model as a dictionary
        """
        return {
            "model": self._model,
            "options": self._options,
            "stop": self._options["stop"],
            "system": self._system_prompt_location if self._use_system else "Disabled",
            "history": self._history_location if self._use_history else "Disabled",
            "identifier": self.identifier,
            "remote": self._remote if self._use_remote else "Disabled"
        }

    def get_options(self) -> dict:
        """
        Get the options of the model
        :return: The options of the model
        """
        return self._options

    def set_option(self, key: str, value: Any) -> bool:
        """
        Set an option of the model with a specific value from the VALID_PARAMETERS
        :param key: The option to set (of the VALID_PARAMETERS)
        :param value: The value to set the option to
        :return: True if the option was set successfully
        """
        if key not in [p["name"] for p in VALID_PARAMETERS]:
            Logger.log(f"Option '{key}' is not a valid parameter", Priority.CRITICAL)
            raise ValueError(f"Option '{key}' is not a valid parameter")

        Logger.log(f"Option {key} is {key in self._options and '' or 'not'} currently in the options",
                   Priority.CRITICAL)

        parameter: dict = list(filter(lambda x: x["name"] == key, VALID_PARAMETERS))[0]
        try:
            cast_type: type = parameter["type"]
            cast_value: cast_type = cast_type(value) # Cast the value to the type of the parameter

            # Check out of bounds
            if parameter["min"] > cast_value or cast_value > parameter["max"]:
                Logger.log(f"Option {key} could not be set to {value}, out of range: {parameter['min']} < {value} < {parameter['max']}", Priority.CRITICAL)
                raise ValueError(f"Expected value between {parameter['min']} and {parameter['max']} but got {value}")

            self._options[key]: cast_type = cast_value # Set the option
            assert type(self._options[key]) == cast_type # Sanity check

            Logger.log(f"Option {key} set to {value}, Attempting type: {cast_type}", Priority.NORMAL)
            Logger.log(f"Option {key} set to {value}", Priority.NORMAL)
            return True
        except TypeError:
            Logger.log(
                f"Option {key} could not be set to {value}, type mismatch: {type(self._options[key])} is not {type(value)}",
                Priority.CRITICAL)
            raise TypeError(f"Expected type {type(self._options[key])} but got {type(value)}")

    def set_system_prompt(self, prompt_file_location: str) -> None:
        """
        Set the system prompt of the model
        :param prompt_file_location: The location of the system prompt file
        """
        self._system_prompt_location = prompt_file_location
        self._system_prompt = load_from_file(prompt_file_location)
        self._use_system = True

    async def generate_async(self, prompt):
        """
        Currently broken smh
        Generate an async response from the model based on the prompt, system prompt and provided history
        :param prompt: The prompt to generate a response from
        :return: Coroutine that generates the response from the model
        """
        Logger.log(f"Generating asynchronous Response using Alpacca model: {self._model}", Priority.NORMAL)
        prompt = self._make_prompt(prompt)
        Logger.log(f"Prompt: {prompt}", Priority.DEBUG)
        iterator = await ollama.AsyncClient().generate(model=self._model, options=self._options, prompt=prompt, stream=True)
        return iterator

    def generate_iterable(self, prompt, rag_context: list[str] = None):
        """
        Generate an iterable response from the model based on the prompt, system prompt and provided history
        :param prompt: The prompt to generate a response from
        :param rag_context: The context gathered using RAG
        :return: An iterable that generates the response from the model
        """
        Logger.log(f"Generating iterable Response using Alpacca model: {self._model}", Priority.NORMAL)
        prompt = self._make_prompt(prompt, rag_context=rag_context)
        Logger.log(f"Prompt: {prompt}", Priority.DEBUG)
        iterator:  GenerateResponse | Iterator[GenerateResponse] = self._client.generate(model=self._model, options=self._options, prompt=prompt, stream=True)
        return iterator

    def _make_prompt(self, prompt: str, rag_context: list[str] = None) -> str:
        context = self._use_history and history_string(self._history) or ""
        system_prompt = self._use_system and self._system_prompt or None
        if system_prompt and "%RAG%" in system_prompt:
            if rag_context is not None:
                Logger.log(f"RAG Context: {rag_context}", Priority.NORMAL)
                system_prompt = system_prompt.replace("%RAG%", " ".join(rag_context))
            else:
                Logger.log("RAG Context is empty", Priority.CRITICAL)

        if system_prompt and "%RPreviousExchange%" in system_prompt:
            system_prompt = system_prompt.replace("%RPreviousExchange%", context)

        if system_prompt and "%UserPrompt%" in system_prompt:
            system_prompt = system_prompt.replace("%UserPrompt%", prompt)

        if not self._use_system:
            return prompt
        return system_prompt

    def get_system_prompt_now(self, rag_context: list[str] = None, prompt: str = "") -> str:
        """
        Get what the ollama model would receive as a prompt if were to generate a response now
        :param rag_context: The context gathered using RAG
        :param prompt: The prompt to generate a response from
        :return: The prompt that the model would receive
        """
        return self._make_prompt(prompt, rag_context)

    def add_history(self, user: str, thoughts: str, answer: str):
        """
        Add a chat exchange to the history
        :param user: The user's input prompt
        :param thoughts: The thoughts of the model
        :param answer: The answer of the model
        """
        if self._use_history:
            self._history.append(ChatExchange(user, thoughts, answer))
        else:
            Logger.log("History is not enabled", Priority.CRITICAL)
            raise Exception("History is not enabled")

    def enable_load_history(self, history_location) -> bool:
        """
        Enable loading history from a file
        :param history_location: The location of the history file
        :return: True if history was loaded
        """
        self._history = [chat_exchange_from_dict(d) for d in load_json(history_location, create=True)]
        self._use_history = True
        return True

    def get_client(self) -> Client:
        """
        Get the client of the model
        :return: The client of the model
        """
        return self._client

    def get_model(self) -> str:
        """
        Get the model of the Alpacca
        :return: The model of the Alpacca
        """
        return self._model

    def get_history(self) -> List[ChatExchange]:
        """
        Get the history of the Alpacca
        :return: The history of the Alpacca
        """
        return self._history

def load_alpacca_from_json(location:str) -> Alpacca:
    """
    Load an Alpacca model from a JSON file
    :param location: The location of the JSON file
    :return: The Alpacca model
    """
    data = load_json(location)
    system = data["system"] if data["system"] != "Disabled" else None
    history = data["history"] if data["history"] != "Disabled" else None
    options = data["options"] if data["options"] != "Disabled" else None
    stop = data["stop"] if data["stop"] else None
    identifier = data["identifier"] if data["identifier"] else None
    remote = data["remote"] if data["remote"] != "Disabled" else None
    return Alpacca(data["model"], stop=stop, system=system, history_location=history, identifier=identifier,
                   host=remote, options=options)

def get_models_from_remote(host: str) -> list[str]:
    """
    Get the models from a remote host
    :param host: The host to get the models from
    :return: The models from the host
    """
    return [m["model"] for m in Client(host=host).list().models]
