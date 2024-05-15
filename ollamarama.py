# ollamarama, chatbot with infinite personalities using local LLMs
# Dustin Whyte
# December 2023

import os
import logging
from rich.console import Console
from litellm import completion
import json

logging.basicConfig(filename='ollamarama.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class ollamarama:
    def __init__(self, personality):

        # holds history
        self.messages = []

        # set default personality
        self.personality = personality
        self.persona(self.personality)

        #load models.json
        with open("models.json", "r") as f:
            self.models = json.load(f)
            f.close()

        #set model
        self.default_model = self.models['llama3']
        self.model = self.default_model

        #i have no idea if these are optimal lol, change these to your liking
        self.temperature = .9
        self.top_p = .7
        self.repeat_penalty = 1.5

    # Sets personality
    def persona(self, persona):
        self.messages.clear()
        personality = "you are " + persona + ". speak in the first person and never break character.  keep your responses brief and to the point. "
        self.messages.append({"role": "system", "content": personality})
        self.messages.append({"role": "user", "content": "introduce yourself"})
    
    # use a custom prompt such as one you might find at awesome-chatgpt-prompts
    def custom(self, prompt):
        self.messages.clear()
        self.messages.append({"role": "system", "content": prompt})

    # respond to messages
    def respond(self, message):
        
        try:
            #Generate response 
            response = completion(
                api_base="http://localhost:11434",
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                messages=message,
                timeout=60
                )
        except:
            return "Something went wrong, try again"
        else:
            #Extract response text and add it to history
            response_text = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": response_text})
            logging.info(f"Bot: {response_text}")
            if len(self.messages) > 30:
                del self.messages[1:3]
            return response_text.strip()
        
    def start(self):
        # text wrap and color
        console = Console()
        console.width=80
        console.wrap_text = True

        def reset():
            logging.info("Bot reset")
            self.model = self.default_model
            self.temperature = .9
            self.top_p = .7
            self.repeat_penalty = 1.5
            # set personality and introduce self
            self.persona(self.personality)
            self.messages.append({"role": "user", "content": "introduce yourself"})
            try:
                console.print("Please wait while the model loads...", style='bold', highlight=False)
                response_text = self.respond(self.messages)
                os.system("clear")
                console.print(response_text + "  Type help for more information.\n", style='gold3', highlight=False)
            # fallback if generated introduction failed
            except:
                console.print("Hello, I am an AI that can assume any personality.  Type help for more information.\n", style='gold3')

        reset()
        
        prompt = "" #empty string for prompt input
        
        while prompt != "quit":
            # get the message
            prompt = console.input("[bold grey66]Prompt: [/]")

            # exit program
            if prompt == "quit" or prompt == "exit":
                exit()
            
            # help menu
            elif prompt == "help":
                console.print('''
[b]reset[/] resets to default personality.
[b]clear[/] resets and clears the screen
[b]stock[/] or [b]default[/] sets bot to stock model settings.
[b]persona[/] activates personality changer, enter a new personality when prompted.
[b]custom[/] set a custom system prompt
[b]change model[/] list models and change current model
[b]reset model[/] reset to default model
[b]change temperature[/] changes temperature
[b]change top_p[/] changes top_p
[b]change repeat_penalty[/] changes repeat_penalty
[b]quit[/] or [b]exit[/] exits the program
''', style="green")
                
            # set personality    
            elif prompt == "persona":
                persona = console.input("[grey66]Persona: [/]") #ask for new persona
                self.persona(persona) #response passed to persona function
                logging.info(f"Persona set to {persona}")
                response = self.respond(self.messages)
                console.print(response + "\n", style="gold3", justify="full", highlight=False) #print response

            # use a custom prompt
            elif prompt == "custom":
                custom = console.input("[grey66]Custom prompt: [/]") #ask for custom prompt
                self.custom(custom)
                logging.info(f"Custom prompt set: {custom}")
                response = self.respond(self.messages)
                console.print(response + "\n", style="gold3", justify="full", highlight=False) #print response

            # reset history   
            elif prompt == "reset":
                logging.info("Bot was reset")
                reset()
            
            elif prompt == "clear":
                os.system('clear')
                logging.info("Bot was reset")
                reset()
                
            # stock model settings    
            elif prompt == "default" or prompt == "stock":
                self.messages.clear()
                logging.info("Stock model settings applied")
                console.print("Stock model settings applied\n", style="green", highlight=False)
            
            elif prompt == "change model":
                console.print(f'''
Current model: {self.model.removeprefix('ollama/')}
Available models: {', '.join(sorted(list(self.models)))}
''', style='green', highlight=False)
                model = console.input("Enter model name: ")
                if model in self.models:
                    self.model = self.models[model]
                    console.print(f"Model set to {self.model.removeprefix('ollama/')}\n", style='green', highlight=False)
                    logging.info(f"Model changed to {self.model.removeprefix('ollama/')}")
            
            elif prompt == "reset model":
                self.model = self.default_model
                logging.info(f"Model changed to {self.model.removeprefix('ollama/')}")

            elif prompt in ["change temperature", "change top_p", "change repeat_penalty"]:
                attr_name = prompt.split()[-1]
                min_val, max_val = {
                    "temperature": (0, 1),
                    "top_p": (0, 1),
                    "repeat_penalty": (0, 2)
                }[attr_name]

                try:
                    value = float(console.input(f"Input {attr_name} between {min_val} and {max_val} (currently {getattr(self, attr_name)}): "))
                    if min_val <= value <= max_val:
                        setattr(self, attr_name, value)
                        console.print(f"{attr_name} set to {value}\n", style='green')
                        logging.info(f"{attr_name.capitalize()} changed to {value}")
                    else:
                        console.print(f"Invalid input, {attr_name} is still {getattr(self, attr_name)}\n", style='green')
                except ValueError:
                    console.print(f"Invalid input, {attr_name} is still {getattr(self, attr_name)}\n", style='green')

            # normal response
            elif prompt != None:
                self.messages.append({"role": "user", "content": prompt})
                logging.info(f"User: {prompt}")
                response = self.respond(self.messages)
                #special colorization for code blocks or quotations
                if "```" in response or response.startswith('"'):
                    console.print(response + "\n", style="gold3", justify="full") 
                #no special colorization for responses without those
                else:
                    console.print(response + "\n", style="gold3", justify="full", highlight=False)
            
            # no message
            else:
                continue

if __name__ == "__main__":
    os.system('clear')
    #set the default personality
    personality = "a minimalist AI assistant"
    #start bot
    bot = ollamarama(personality)
    bot.start()
