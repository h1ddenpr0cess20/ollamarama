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

class ollamarama:
    def __init__(self):
        # holds history
        self.messages = []

        #load config
        with open("config.json", "r") as f:
            self.config = json.load(f)
            f.close()

        #set model
        self.models = self.config['models']
        self.default_model = self.config['default_model']
        self.model = self.models[self.default_model]

        self.api_url = self.config['api_base'] + "/api/chat"
        self.temperature, self.top_p, self.repeat_penalty = self.config['options'].values()
        self.defaults = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repeat_penalty": self.repeat_penalty
        }

        self.default_personality = self.config["personality"]
        self.personality = self.default_personality
        self.prompt = self.config["prompt"]
        self.persona(self.personality)

    # Sets personality
    def persona(self, persona):
        self.messages.clear()
        personality = self.prompt[0] + persona + self.prompt[1]
        self.messages.append({"role": "system", "content": personality})
        self.messages.append({"role": "user", "content": "introduce yourself"})
    
    def custom(self, system):
        self.messages.clear()
        self.messages.append({"role": "system", "content": system})
        self.messages.append({"role": "user", "content": "introduce yourself"})

    # respond to messages
    def respond(self, message):
        try:
            data = {
                "model": self.model, 
                "messages": message, 
                "stream": False,
                "options": {
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                    "repeat_penalty": self.repeat_penalty
                    }
                }
        except:
            return "Something went wrong, try again"
        else:
            response = requests.post(self.api_url, json=data, timeout=60)
            response.raise_for_status()
            data = response.json()
            response_text = data["message"]["content"].strip('"').strip()
            self.messages.append({"role": "assistant", "content": response_text})
            logging.info(f"Bot: {response_text}")
            if len(self.messages) > 30:
                if self.messages[0]['role'] == "system":
                    del self.messages[1:3]
                else:
                    del self.messages[0:2]
            return response_text
        
    def start(self):
        console = Console(width=120, highlight=False)
        
        history = InMemoryHistory()
        session = PromptSession(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter([
                "help", "exit", "quit", "reset", "clear", 
                "stock", "persona", "custom", "change model", 
                "change temperature", "change top_p", "change repeat_penalty", 
                "reset model"]) #sorta distracting, may want to disable
        )
        persona_history = InMemoryHistory()
        persona_session = PromptSession(
            history=persona_history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(['a sarcastic jerk',]) #callback to jerkbot, my original chatbot.  add whatever personas you'd like here
        )
        custom_history = InMemoryHistory()
        custom_session = PromptSession(
            history=custom_history,
            auto_suggest=AutoSuggestFromHistory(),
        )
        model_history = InMemoryHistory()
        model_session = PromptSession(
            history=model_history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(self.models)
        )

        def reset():
            logging.info("Bot reset")
            self.model = self.models[self.default_model]
            self.temperature, self.top_p, self.repeat_penalty = self.defaults.values()
            # set personality and introduce self
            self.persona(self.personality)
            self.messages.append({"role": "user", "content": "introduce yourself"})
            try:
                console.print("Please wait while the model loads...", style='bold')
                response_text = self.respond(self.messages)
                os.system("clear")
                console.print(Markdown(response_text + "  Type help for more information."), style='gold3')
            # fallback if generated introduction failed
            except Exception as e:
                console.print(e)
                exit()                

        reset()
        
        message = ""
        while message != "quit":
            # get the message
            message = session.prompt("> ")

            # exit program
            if message == "quit" or message == "exit":
                exit()
            
            # help menu
            elif message == "help":
                with open("help.txt", "r") as f:
                    help_text = f.read()
                    f.close()
                console.print(help_text)
                
            # set personality    
            elif message == "persona":
                persona = persona_session.prompt("Persona: ")
                if persona != "":
                    self.persona(persona)
                    logging.info(f"Persona set to {persona}")
                    response = self.respond(self.messages)
                    console.print(response, style="gold3", justify="full")

            # use a custom prompt
            elif message == "custom":
                custom = custom_session.prompt("System prompt: ")
                if custom != "":
                    self.custom(custom)
                    logging.info(f"Custom system prompt set: {custom}")
                    response = self.respond(self.messages)
                    console.print(response, style="gold3", justify="full") 

            # reset history   
            elif message == "reset":
                logging.info("Bot was reset")
                reset()
            
            elif message == "clear":
                os.system('clear')

            # stock model settings    
            elif message == "default" or message == "stock":
                self.messages.clear()
                logging.info("Stock model settings applied")
                console.print("Stock model settings applied", style="green")
            
            elif message == "change model":
                console.print(f"[bold green]Current model[/]: [bold]{self.model}[/]")
                console.print(f"[bold green]Available models[/]: {', '.join(sorted(list(self.models)))}")
                model = model_session.prompt("Enter model name: ")
                if model in self.models:
                    self.model = self.models[model]
                    console.print(f"Model set to {self.model}", style='green')
                    logging.info(f"Model changed to {self.model}")
            
            elif message == "reset model":
                self.model = self.models[self.default_model]
                logging.info(f"Model changed to {self.model}")

            elif message in ["change temperature", "change top_p", "change repeat_penalty"]:
                attr_name = message.split()[-1]
                min_val, max_val = {
                    "temperature": (0, 1),
                    "top_p": (0, 1),
                    "repeat_penalty": (0, 2)
                }[attr_name]

                try:
                    value = float(console.input(f"Input {attr_name} between {min_val} and {max_val} (currently {getattr(self, attr_name)}): "))
                    if min_val <= value <= max_val:
                        setattr(self, attr_name, value)
                        console.print(f"{attr_name} set to {value}", style='green')
                        logging.info(f"{attr_name.capitalize()} changed to {value}")
                    else:
                        console.print(f"Invalid input, {attr_name} is still {getattr(self, attr_name)}", style='green')
                except ValueError:
                    console.print(f"Invalid input, {attr_name} is still {getattr(self, attr_name)}", style='green')

            # normal response
            elif message != None:
                self.messages.append({"role": "user", "content": message})
                logging.info(f"User: {message}")
                response = self.respond(self.messages)
                console.print(Markdown(response), style="gold3")
            # no message
            else:
                continue

if __name__ == "__main__":
    os.system('clear')
    logging.basicConfig(filename='ollamarama.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    bot = ollamarama()
    bot.start()
