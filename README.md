# ollamarama
Terminal based AI chatbot with infinite personalities, using local LLMs

This is basically just Ollama with model switching and personality switching.  I like to call it the poor man's mixture of experts.

## Setup

Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run offline LLMs, etc.

You can install it with this command:
```
curl https://ollama.ai/install.sh | sh
```

Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.  Add those to the self.models dictionary.  If you want to use the ones I've included, just run the commands in the models.md file.  You can skip this part, and they should download when the model is switched, but the response will be delayed until it finishes downloading.

You'll also need to install rich and litellm
```
pip3 install rich litellm
```

## Use

```
python3 ollamarama.py
```

**help** shows the help menu

**reset**  resets to default personality

**stock** or **default**  sets bot to stock gpt settings

**persona**  activates personality changer

**custom**  use a custom system prompt

**list models** list available models

**change model** change the current model

**quit** or **exit** exits the program
