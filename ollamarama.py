# ollamarama, chatbot with infinite personalities using local LLMs
# Dustin Whyte
# December 2023


import os
import logging
from rich.console import Console
from litellm import completion

logging.basicConfig(filename='ollamarama.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class ollamarama:
    def __init__(self, personality):

        # holds history
        self.messages = []

        # set default personality
        self.personality = personality
        self.persona(self.personality)

        #put the models you want to use here, still testing various models
        self.models = {
            'zephyr': 'ollama/zephyr:7b-beta-q8_0',
            'solar': 'ollama/solar',
            'mistral': 'ollama/mistral',
            'llama2': 'ollama/llama2',
            'llama2-uncensored': 'ollama/llama2-uncensored',
            'openchat': 'ollama/openchat',
            'codellama': 'ollama/codellama:13b-instruct-q4_0',
            'dolphin-mistral': 'ollama/dolphin2.2-mistral:7b-q8_0',
            'deepseek-coder': 'ollama/deepseek-coder:6.7b',
            'orca2': 'ollama/orca2',
            'starling-lm': 'ollama/starling-lm',
            'vicuna': 'ollama/vicuna:13b-q4_0',
            'phi': 'ollama/phi',
            'orca-mini': 'ollama/orca-mini',
            'wizardcoder': 'ollama/wizardcoder:python',
            'stablelm-zephyr': 'ollama/stablelm-zephyr',
            'neural-chat': 'ollama/neural-chat',
            'mistral-openorca': 'ollama/mistral-openorca',
            'deepseek-llm': 'ollama/deepseek-llm:7b-chat',
            'wizard-vicuna-uncensored': 'ollama/wizard-vicuna-uncensored'
        }
        #set model
        self.default_model = self.models['solar']
        self.model = self.default_model

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
                temperature=.9,
                top_p=.7,
                repeat_penalty=1.5,
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
        soft_wrap=True
       
        def reset():
            logging.info("Bot reset")
            os.system('clear') #clear screen
            self.model = self.default_model
            # set personality and introduce self
            self.persona(self.personality)
            self.messages.append({"role": "user", "content": "introduce yourself [your response must be one paragraph or less]"})
            try:
                response_text = self.respond(self.messages)
                console.print(response_text + "  Type help for more information.\n", style='gold3')
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
[b]stock[/] or [b]default[/] sets bot to stock gpt settings.
[b]persona[/] activates personality changer, enter a new personality when prompted.
[b]custom[/] set a custom prompt
[b]change model[/] list models and change current model
[b]reset model[/] reset to default model
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
                
            # stock model settings    
            elif prompt == "default" or prompt == "stock":
                self.messages.clear()
                logging.info("Stock model settings applied")
                console.print("Stock model settings applied\n", style="green")
            
            elif prompt == "change model":
                console.print(f'''
Current model: {self.model.removeprefix('ollama/')}
Available models: {', '.join(sorted(list(self.models)))}
''', style='green')
                model = console.input("Enter model name: ")
                if model in self.models:
                    self.model = self.models[model]
                    console.print(f"Model set to {self.model.removeprefix('ollama/')}\n", style='green', highlight=False)
            
            elif prompt == "reset model":
                self.model = self.default_model


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
       
    #set the default personality
    personality = "a helpful and thorough AI assistant who provides accurate and detailed answers without being too verbose"
    #start bot
    bot = ollamarama(personality)
    bot.start()
