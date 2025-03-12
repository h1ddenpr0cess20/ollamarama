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
    """
    This class handles the initialization of the chatbot, loading configurations,
    managing models and options, interacting with the Ollama API, and running the
    main loop for user interaction.

    Attributes:
        console (Console): Rich Console instance for styled output.
        messages (list): List of message dictionaries for conversation history.
        config (dict): Configuration loaded from config.json.
        models (dict): Dictionary of available models.
        default_model (str): Name of the default model.
        model (str): Name of the currently selected model.
        api_url (str): URL for the Ollama API.
        options (dict): Dictionary of model options (temperature, top_p, etc.).
        defaults (dict): Default values for model options.
        default_personality (str): Default chatbot personality.
        personality (str): Currently selected chatbot personality.
        prompt (str): Base prompt for the chatbot.
        kb (KeyBindings): Keybindings for the prompt session.
        session (PromptSession): Prompt Toolkit session for user input.
        persona_session (PromptSession): Prompt Toolkit session for persona input.
        custom_session (PromptSession): Prompt Toolkit session for custom input.
        model_session (PromptSession): Prompt Toolkit session for model selection.

    
    """
    def __init__(self):
        """Initialize the ollamarama chatbot."""
        logging.basicConfig(filename='ollamarama.log', level=logging.INFO, format='%(asctime)s - %(message)s')
        
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
        
        self.kb = KeyBindings()
        
        @self.kb.add('escape', 'enter')
        def _(event):
            """Add a newline when Escape+Enter is pressed."""
            event.current_buffer.insert_text('\n')

        @self.kb.add('enter')
        def _(event):
            """Submit input when Enter is pressed."""
            event.current_buffer.validate_and_handle()
            
        self.session = self.create_session(
            InMemoryHistory(),
            multiline=True,
            completer=WordCompleter([
                "/help", "/exit", "/quit", "/reset", "/clear", 
                "/stock", "/persona", "/custom", "/model", 
                "/temperature", "/top_p", "/repeat_penalty"
            ])
        )

        self.persona_session = self.create_session(
            InMemoryHistory(),
            multiline=True,
            completer=WordCompleter(
                ['a sarcastic jerk'],  # callback to jerkbot, my original chatbot project. add whatever personas you'd like here, or remove completely if you don't want them
                match_middle=True
            )
        )

        self.custom_session = self.create_session(
            InMemoryHistory(),
            multiline=True
        )

        self.model_session = self.create_session(
            InMemoryHistory(),
            completer=WordCompleter(self.models.keys())
        )

    def create_session(self, history, **kwargs):
        """Create a prompt session with the specified history and options.
        
        Args:
            history: The history object to use for the session
            **kwargs: Additional arguments to pass to PromptSession
            
        Returns:
            PromptSession: The created prompt session
        """
        return PromptSession(
            key_bindings=self.kb,
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            **kwargs
        )

    def set_prompt(self, persona=False, custom=False):
        """Sets the system prompt for the chatbot.

        Args:
            persona (bool or str, optional): If True, prompts the user to enter a persona.
                If a string, sets the persona to the given string. Defaults to False.
            custom (bool, optional): If True, prompts the user to enter a custom system prompt. Defaults to False.
        """
        self.messages.clear()
        if persona:
            if isinstance(persona, bool):
                if persona:
                    personality = self.persona_session.prompt("Persona: ")
            else:
                personality = persona
            if personality != "":
                system = self.prompt[0] + personality + self.prompt[1]
                logging.info(f"Persona set to {system}")
            else:
                system = False
        elif custom:
            system = self.custom_session.prompt("System prompt: ")
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
            self.console.print(response, style="gold3", justify="left")

    def respond(self, message):
        """Sends a message to the chatbot model and returns the response.

        Args:
            message (list): The list of messages in the conversation history.

        Returns:
            str: The chatbot's response.
        """
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
            try:
                response = requests.post(self.api_url, json=data, timeout=180)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                error_message = f"Request failed: {e}"
                self.console.print(error_message, style="red")
                logging.error(error_message)
                return "Failed to get response from the model."
            except json.JSONDecodeError as e:
                error_message = f"Failed to decode JSON response: {e}"
                self.console.print(error_message, style="red")
                logging.error(error_message)
                return "Received invalid data from the model."
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                self.console.print(error_message, style="red")
                logging.exception(error_message)
                return "An unexpected error occurred. Check the logs for details."
            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
            self.messages.append({"role": "assistant", "content": response_text})
            logging.info(f"Bot: {response_text}")

            if len(self.messages) > 24:
                if self.messages[0]['role'] == "system":
                    self.messages.pop(1)
                else:
                    self.messages.pop(0)
            return response_text.strip()

    def reset(self):
        """Resets the chatbot to its default state, loading the default model and personality."""
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
        """Changes the chatbot model.

        Args:
            reset (bool, optional): If True, resets the model to the default model. Defaults to False.
        """
        if reset:
            self.model = self.models[self.default_model]
            self.console.print(f"Model set to {self.model}", style='green')
            logging.info(f"Model changed to {self.model}")
        else:
            self.console.print(f"[bold green]Current model[/]: [bold]{self.model}[/]")
            self.console.print(f"[bold green]Available models[/]: {', '.join(sorted(list(self.models)))}")
            model = self.model_session.prompt("Enter model name: ")
            if model in self.models:
                self.model = self.models[model]
                self.console.print(f"Model set to {self.model}", style='green')
                logging.info(f"Model changed to {self.model}")

    def change_option(self, option):
        """Changes a model option (temperature, top_p, repeat_penalty).

        Args:
            option (str): The name of the option to change.
        """
        values = {
            "temperature": (0, 1),
            "top_p": (0, 1),
            "repeat_penalty": (0, 2)
        }

        try:
            input_value = self.console.input("Input new value: ")
            if not input_value.strip():
                self.console.print("No value entered, nothing changed", style='red')
                return
                
            value = float(input_value)
            if value >= values[option][0] and value <= values[option][1]:
                self.options[option] = value
                self.console.print(f"{option.capitalize()} set to {value}", style='green')
            else:
                self.console.print(f"Invalid value. Must be between {values[option][0]} and {values[option][1]}", style='red')
        except ValueError:
            self.console.print("Invalid input. Please enter a numeric value.", style='red')

    def help_menu(self):
        """Displays the help menu from help.txt."""
        with open("help.txt", "r") as f:
            help_text = f.read()
            f.close()
        self.console.print(help_text)

    def start(self):
        """Starts the main loop of the chatbot."""
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
            message = self.session.prompt("> ")
            if message in commands:
                command = commands[message]
                command()
            elif message != None:
                self.messages.append({"role": "user", "content": message})
                logging.info(f"User: {message}")
                response = self.respond(self.messages)
                self.console.print(Markdown(response, inline_code_lexer="python", inline_code_theme="monokai", code_theme="monokai", justify="left"), style="gold3")

if __name__ == "__main__":
    bot = ollamarama()
    bot.start()
