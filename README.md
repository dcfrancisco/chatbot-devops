# chatbot-devops

## Table of Contents

- [chatbot-devops](#chatbot-devops)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
    - [Build a chatbot using Rasa framework](#build-a-chatbot-using-rasa-framework)
  - [Setup Python environment](#setup-python-environment)
    - [Install Python 3.9](#install-python-39)
    - [Install pip](#install-pip)
    - [Install virtualenv](#install-virtualenv)
    - [Create a virtual environment](#create-a-virtual-environment)
    - [Activate the virtual environment](#activate-the-virtual-environment)
    - [Deactivate the virtual environment](#deactivate-the-virtual-environment)
  - [Installation](#installation)
    - [Install Rasa](#install-rasa)
  - [Rasa](#rasa)
    - [Train nlu](#train-nlu)
    - [Train](#train)
    - [Run](#run)
    - [Run with debug](#run-with-debug)
    - [Run action server](#run-action-server)


## Description

This repository showcases the capabilities of Natural Language Understanding (NLU), a subset of Generative AI. It leverages the Rasa framework, a Conversational AI chatbot, integrated with Jenkins and the Gradio interface. The goal is to facilitate engaging and accurate conversational experiences while demonstrating the power of modern AI-driven CI/CD pipelines.

### Build a chatbot using Rasa framework

## Setup Python environment

### Install Python 3.9

```bash
sudo apt-get install python3.9

python3.9 -m venv venv

source venv/bin/activate

```

### Install pip

```bash
sudo apt-get install python3-pip
```

### Install virtualenv

```bash
sudo pip3 install virtualenv
```

### Create a virtual environment

```bash
virtualenv -p python3.7 venv
```

### Activate the virtual environment

```bash
source venv/bin/activate
```

### Deactivate the virtual environment

```bash
deactivate
```

python3.9 -m venv venv
source venv/bin/activate
python3.9 -m venv rasa-env\
python3.9 -m venv venv
source venv/bin/activate



## Installation

### Install Rasa

```bash
pip install rasa
```

## Rasa

### Train nlu


### Train


### Run


### Run with debug



### Run action server


```

rasa run -m models --enable-api --cors "*" --debug
rasa train nlu
rasa run -m models --enable-api --cors "*" --debug
rasa train 
rasa run -m models --enable-api --cors "*" --debug
rasa run -m models --enable-api --cors "*"
rasa run -m models --enable-api --cors "*"
rasa train 
rasa run -m models --enable-api --cors "*"
rasa run -m models --enable-api --cors "*"
rasa run -m models --enable-api --cors "*"
rasa run -m models --enable-api --cors "*"
cd rasa

```