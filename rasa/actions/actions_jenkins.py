import requests
import os
import base64
from typing import Any, Dict, List, Text, Union
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv


class ActionListJobs(Action):
    def name(self) -> Text:
        return "action_list_jobs_jenkins"

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
            "http://localhost:8080/api/json", auth=auth, headers=headers, timeout=5
        )
        print(username)
        print(password)

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

        return []


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
        response = requests.post("http://localhost:8080/createJob", json=job_payload)

        if response.status_code == 200:
            dispatcher.utter_message(text="Job created successfully.")
        else:
            dispatcher.utter_message(text="Failed to create the job in Jenkins.")

        # Reset slots after completing the action
        return [AllSlotsReset()]
