# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import requests
import os
import base64
from typing import Any, Text, Dict, List
import random
from typing import Any, Dict, List, Text, Union
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.events import FollowupAction
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# computer_choice & determine_winner functions refactored from
# https://github.com/thedanelias/rock-paper-scissors-python/blob/master/rockpaperscissors.py, MIT liscence


class ActionPlayRPSLS(Action):
    def name(self) -> Text:
        return "action_play_rpsls"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        choices = ["rock", "paper", "scissors", "spock", "lizard"]
        computer_choice = random.choice(choices)

        user_choice = tracker.latest_message["text"]
        user_choice = user_choice.lower()

        if user_choice not in choices:
            dispatcher.utter_message(
                "Sorry, I didn't understand your choice. Please try again."
            )
            return []

        dispatcher.utter_message(f"You chose {user_choice.capitalize()}")
        dispatcher.utter_message(f"The computer chose {computer_choice.capitalize()}")

        if user_choice == computer_choice:
            dispatcher.utter_message("It's a tie!")
        elif (
            (
                user_choice == "rock"
                and (computer_choice == "scissors" or computer_choice == "lizard")
            )
            or (
                user_choice == "paper"
                and (computer_choice == "rock" or computer_choice == "spock")
            )
            or (
                user_choice == "scissors"
                and (computer_choice == "paper" or computer_choice == "lizard")
            )
            or (
                user_choice == "spock"
                and (computer_choice == "rock" or computer_choice == "scissors")
            )
            or (
                user_choice == "lizard"
                and (computer_choice == "paper" or computer_choice == "spock")
            )
        ):
            win_message = f"Congratulations! {user_choice.capitalize()} {self.get_win_message(user_choice, computer_choice)}"
            dispatcher.utter_message(win_message)
        else:
            lose_message = f"Sorry, the computer wins! {computer_choice.capitalize()} {self.get_win_message(computer_choice, user_choice)}"
            dispatcher.utter_message(lose_message)

        return [FollowupAction("utter_play_again")]

    @staticmethod
    def get_win_message(winning_choice: Text, losing_choice: Text) -> Text:
        rules = {
            "rock": {"scissors": "crushes", "lizard": "crushes"},
            "paper": {"rock": "covers", "spock": "disproves"},
            "scissors": {"paper": "cuts", "lizard": "decapitates"},
            "spock": {"rock": "vaporizes", "scissors": "smashes"},
            "lizard": {"paper": "eats", "spock": "poisons"},
        }

        if winning_choice in rules and losing_choice in rules[winning_choice]:
            # return f"{winning_choice.capitalize()} {rules[winning_choice][losing_choice]} {losing_choice}."
            return f"{rules[winning_choice][losing_choice]} {losing_choice}."

        return ""


class ActionListJobs(Action):
    def name(self) -> Text:
        return "action_list_jobs"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        load_dotenv()

        # Get the username and password from the environment variables
        username = os.getenv("JENKINS_USERNAME")
        password = os.getenv("JENKINS_PASSWORD")
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(
            credentials.encode()
        ).decode()  # base64 encoding

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
        }

        auth = HTTPBasicAuth(username, password)

        # Make a request to the Jenkins API to get the list of jobs
        response = requests.get(
            "http://localhost:8080/api/json", headers=headers, auth=auth, timeout=5
        )

        print(response.status_code)
        print(response.json())
        if response.status_code == 200:
            jobs = response.json().get("jobs", [])

            if jobs:
                job_names = [job["name"] for job in jobs]
                jobs_text = ", ".join(job_names)

                dispatcher.utter_message(
                    text=f"Here are the available jobs: {jobs_text}"
                )
            else:
                dispatcher.utter_message(text="No jobs found in Jenkins.")
        else:
            dispatcher.utter_message(text="Failed to retrieve jobs from Jenkins.")

        return []  # No events are produced by this action


class ActionCreateJob(Action):
    def name(self) -> Text:
        return "action_create_job"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        job_name = tracker.get_slot("job_name")
        job_description = tracker.get_slot("job_description")
        job_config = tracker.get_slot("job_config")

        # Prepare the request payload to create the job
        job_payload = {
            "name": job_name,
            "description": job_description,
            "config": job_config,
        }

        # Make a request to the Jenkins API to create the job
        response = requests.post("https://your-jenkins-url/createJob", json=job_payload)

        if response.status_code == 200:
            dispatcher.utter_message(text="Job created successfully.")
        else:
            dispatcher.utter_message(text="Failed to create the job in Jenkins.")

        # Reset slots after completing the action
        return [AllSlotsReset()]


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionAskJobName(Action):
    def name(self) -> Text:
        return "action_ask_job_name"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Implement your logic here

        return []


class ActionAskJobDescription(Action):
    def name(self) -> Text:
        return "action_ask_job_description"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Implement your logic here

        return []


class ActionAskJobConfig(Action):
    def name(self) -> Text:
        return "action_ask_job_config"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Implement your logic here

        return []


class ActionConfirmCreateJob(Action):
    def name(self) -> Text:
        return "action_confirm_create_job"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Implement your logic here

        return []
