# ollamarama, chatbot with infinite personalities using local LLMs
# Dustin Whyte
# December 2023

import os
import logging
import requests
import json
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import prompt, PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings


class ollamarama:
    def __init__(self):
        self.console = Console(width=120, highlight=False)

        self.messages = []

        with open("config.json", "r") as f:
            self.config = json.load(f)
            f.close()

        self.models = self.config['models']
        self.default_model = self.config['default_model']
        self.model = self.models[self.default_model]

        self.api_url = self.config['api_base'] + "/api/chat"
        self.options = self.config['options']
        self.defaults = self.options

        self.default_personality = self.config["personality"]
        self.personality = self.default_personality
        self.prompt = self.config["prompt"]

    def set_prompt(self, persona=False, custom=False):
        self.messages.clear()
        if persona:
            if isinstance(persona, bool):
                if persona:
                    personality = persona_session.prompt("Persona: ")
            else:
                personality = persona
            if personality != "":
                system = self.prompt[0] + personality + self.prompt[1]
                logging.info(f"Persona set to {system}")
            else:
                system = False
        elif custom:
            system = custom_session.prompt("System prompt: ")
            if system != "":
                logging.info(f"Custom system prompt set: {system}")
            else:
                system = False
        else:
            system = False
            logging.info("Stock model settings applied")
            self.console.print("Stock model settings applied", style="green")
        if system:
            self.messages.append({"role": "system", "content": system})
            self.messages.append({"role": "user", "content": "introduce yourself"})
            response = self.respond(self.messages)
            self.console.print(response, style="gold3", justify="full")

    def respond(self, message):
        try:
            data = {
                "model": self.model, 
                "messages": message, 
                "stream": False,
                "options": self.options
                }
        except:
            return "Something went wrong, try again"
        else:
            response = requests.post(self.api_url, json=data, timeout=60)
            response.raise_for_status()
            data = response.json()
            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
            self.messages.append({"role": "assistant", "content": response_text})
            logging.info(f"Bot: {response_text}")
            
            if len(self.messages) > 30:
                if self.messages[0]['role'] == "system":
                    del self.messages[1:3]
                else:
                    del self.messages[0:2]
            return response_text.strip()
        
    def reset(self):
        logging.info("Bot reset")
        self.model = self.models[self.default_model]
        self.options = self.defaults
        try:
            self.console.print("Please wait while the model loads...", style='bold')
            self.set_prompt(persona=self.personality)
        except Exception as e:
            self.console.print(e)
            exit()

    def change_model(self, reset=False):
        if reset:
            self.model = self.models[self.default_model]
            self.console.print(f"Model set to {self.model}", style='green')
            logging.info(f"Model changed to {self.model}")
        else:
            self.console.print(f"[bold green]Current model[/]: [bold]{self.model}[/]")
            self.console.print(f"[bold green]Available models[/]: {', '.join(sorted(list(self.models)))}")
            model = model_session.prompt("Enter model name: ")
            if model in self.models:
                self.model = self.models[model]
                self.console.print(f"Model set to {self.model}", style='green')
                logging.info(f"Model changed to {self.model}")
    
    def change_option(self, option):
        values = {
            "temperature": (0, 1),
            "top_p": (0, 1),
            "repeat_penalty": (0, 2)
        }
        
        value = int(self.console.input("Input new value: "))
        if value >= values[option][0] and value <= values[option][1]:
                self.options[option] = value
                self.console.print(f"{option.capitalize()} set to {value}", style='green')
        else:
            self.console.print("Invalid value, nothing changed", style='red')

    def help_menu(self):
            with open("help.txt", "r") as f:
                help_text = f.read()
                f.close()
            self.console.print(help_text)

    def start(self):
        self.reset()
        
        commands = {
            "/quit": lambda: exit(),
            "/exit": lambda: exit(),
            "/help": lambda: self.help_menu(),
            "/reset": lambda: self.reset(),
            "/stock": lambda: self.set_prompt(),
            "/clear": lambda: os.system('clear'),
            "/persona": lambda: self.set_prompt(persona=True),
            "/custom": lambda: self.set_prompt(custom=True),
            "/model": lambda: self.change_model(),
            "/model reset": lambda: self.change_model(reset=True),
            "/temperature": lambda: self.change_option("temperature"),
            "/top_p": lambda: self.change_option("top_p"),
            "/repeat_penalty": lambda: self.change_option("repeat_penalty"),
        }

        message = ""
        while True:
            message = session.prompt("> ")
            if message in commands:
                command = commands[message]
                command()
            elif message != None:
                self.messages.append({"role": "user", "content": message})
                logging.info(f"User: {message}")
                response = self.respond(self.messages)
                self.console.print(Markdown(response), style="gold3")

if __name__ == "__main__":
    bot = ollamarama()

    kb = KeyBindings()
    @kb.add('escape', 'enter')
    def _(event):
        event.current_buffer.insert_text('\n')

    @kb.add('enter')
    def _(event):
        event.current_buffer.validate_and_handle()

    history = InMemoryHistory()
    session = PromptSession(
        key_bindings=kb,
        history=history,
        multiline=True,
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(words=[
            "/help", "/exit", "/quit", "/reset", "/clear", 
            "/stock", "/persona", "/custom", "/model", 
            "/temperature", "/top_p", "/repeat_penalty", 
            ], 
            )
    )
    persona_history = InMemoryHistory()
    persona_session = PromptSession(
        key_bindings=kb,
        history=persona_history,
        multiline=True,
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(['a sarcastic jerk',], #callback to jerkbot, my original chatbot.  add whatever personas you'd like here
                                match_middle=True), 
    )
    custom_history = InMemoryHistory()
    custom_session = PromptSession(
        key_bindings=kb,
        history=custom_history,
        multiline=True,
        auto_suggest=AutoSuggestFromHistory(),
    )
    model_history = InMemoryHistory()
    model_session = PromptSession(
        key_bindings=kb,
        history=model_history,
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(bot.models.keys())
    )

    logging.basicConfig(filename='ollamarama.log', level=logging.INFO, format='%(asctime)s - %(message)s')
    bot.start()
