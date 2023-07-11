FROM rasa/rasa-sdk:3.6.0

WORKDIR /app

COPY actions.py /app/actions/actions.py
COPY actions_jenkins.py /app/actions/actions_jenkins.py
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

USER 1001
# CMD ["start", "--actions", "actions"]
# ENTRYPOINT ["rasa", "run", "actions", "--debug"]
# ENTRYPOINT ["rasa", "run", "actions", "--actions", "actions"]