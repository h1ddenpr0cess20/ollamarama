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
        self.default_model = self.models['mistral']
        self.model = self.default_model

        #i have no idea if these are optimal lol, change these to your liking
        self.temperature = .9
        self.top_p = .7
        self.repeat_penalty = 1.5

    # Sets personality
    def persona(self, persona):
        self.messages.clear()
        personality = "you are " + persona + ". speak in the first person and never break character."
        self.messages.append({"role": "system", "content": personality})
        self.messages.append({"role": "user", "content": "introduce yourself [your response must be one paragraph or less]"})
    
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
            self.messages.append({"role": "user", "content": "introduce yourself [your response must be one paragraph or less]"})
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

            elif prompt == "change temperature":
                try:
                    temp = float(console.input(f"Input temperature between 0 and 1 (currently {self.temperature}): "))
                    if 0 <= temp <=1:
                        self.temperature = temp
                        console.print(f"Temperature set to {self.temperature}\n", style='green')
                        logging.info(f"Temperature changed to {self.temperature}")
                    else:
                        console.print(f"Invalid input, temperature is still {self.temperature}\n", style='green')
                except ValueError:
                        console.print(f"Invalid input, temperature is still {self.temperature}\n", style='green')

            elif prompt == "change top_p":
                try:
                    top_p = float(console.input(f"Input top_p between 0 and 1 (currently {self.top_p}): "))
                    if 0 <= top_p <=1:
                        self.top_p = top_p
                        console.print(f"top_p set to {self.top_p}\n", style='green')
                        logging.info(f"Top_p changed to {self.top_p}")
                    else:
                        console.print(f"Invalid input, top_p is still {self.top_p}\n", style='green')
                except ValueError:
                        console.print(f"Invalid input, top_p is still {self.top_p}\n", style='green')

            elif prompt == "change repeat_penalty":
                try:
                    repeat_penalty = float(console.input(f"Input top_p between 0 and 2 (currently {self.repeat_penalty}): "))
                    if 0 <= repeat_penalty <=2:
                        self.repeat_penalty = repeat_penalty
                        console.print(f"repeat_penalty set to {self.repeat_penalty}\n", style='green')
                        logging.info(f"Repeat_penalty changed to {self.repeat_penalty}")
                    else:
                        console.print(f"Invalid input, repeat_penalty is still {self.repeat_penalty}\n", style='green')
                except ValueError:
                        console.print(f"Invalid input, repeat_penalty is still {self.repeat_penalty}\n", style='green')


            # normal response
            elif prompt != None:
                self.messages.append({"role": "user", "content": prompt + " [your response must be one paragraph or less]"})
                logging.info(f"User: {prompt}")
                response = self.respond(self.messages)
                #special colorization for code blocks or quotations
                if "```" in response or response.startswith('"'):
                    console.print(response + "\n", style="gold3", justify="full") #print response
                #no special colorization for responses without those
                else:
                    console.print(response + "\n", style="gold3", justify="full", highlight=False) #print response
            
            # no message
            else:
                continue

if __name__ == "__main__":
    os.system('clear')
    #set the default personality
    personality = "a helpful and thorough AI assistant who provides accurate and detailed answers without being too verbose"
    #start bot
    bot = ollamarama(personality)
    bot.start()
