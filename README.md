# ollamarama
Terminal based AI chatbot with infinite personalities, using local LLMs with Ollama and LiteLLM.  

This is basically just Ollama with model switching and personality switching.  I like to call it the poor man's mixture of experts.

Also available for [IRC](https://github.com/h1ddenpr0cess20/ollamarama-irc) and [Matrix](https://github.com/h1ddenpr0cess20/ollamarama-matrix) chat protocols.

## Setup

Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run offline LLMs, etc.

You can install it with this command:
```
curl https://ollama.ai/install.sh | sh
```

Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.   Add those to the models.json file.  If you want to use the ones I've included, just run ollama pull _modelname_ for each.  You can skip this part, and they should download when the model is switched, but the response will be delayed until it finishes downloading.

You'll also need to install rich and litellm
```
pip3 install rich litellm
```

## Use

```
python3 ollamarama.py
```

**help**  shows the help menu

**reset**  resets to default personality

**clear**  resets and clears the screen

**stock**  or **default**  sets bot to stock model settings

**persona**  activates personality changer

**custom**  use a custom system prompt

**change model**  list models and change the current model

**reset model**  reset to default model

**change temperature**  changes temperature

**change top_p**  changes top_p

**change repeat_penalty**  changes repeat_penalty

**quit** or **exit**  exits the program
