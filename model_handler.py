import json
import requests
from slack_handler import SlackBotManager
from RAG.rag_handler import RAGHandler
import re
import os
import gradio as gr
import shutil


# Constants
OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "llama3.2"
os.environ["ALLOW_RESET"] = "TRUE"

class ModelHandler:
    def __init__(self, localAPIUrl, model):
        self.localAPIUrl = localAPIUrl
        self.model = model
        self.header = {"Content-Type": "application/json"}
        self.rag_handler = RAGHandler()
        self.slack_manager = SlackBotManager()

    def _is_clear_history_request(self, message):
        """
        Check if the user wants to clear history and data.
        """
        return any(keyword in message.lower() for keyword in ["clear history", "clear data", "reset context"])

    def _is_slack_channel_request(self, message):
        """
        Check if the message is about analyzing a Slack channel.
        """
        return "analyze slack channel" in message.lower() or "analyze channel" in message.lower()
    
    def _is_slack_channel_listing_request(self, message):
        """
        Check if the message is about listing out Slack channels.
        """
        return "channels" in message.lower() and ("list" in message.lower() or "find" in message.lower())
    
    def _is_describe_request(self, message):
        """
        Check if user message request channel description and short summary
        """
   
        if "describe slack channel" in message.lower():
            return True
    
        return False


    def extract_channel_name(self, message):
        """
        Extract Slack channel name from the user message.
        """
        match = re.search(r"#(\w+)", message)
        return match.group(1) if match else None
    

    def delete_directory_with_files(self, directory_path):
        """
        Deletes all files and subdirectories in a given directory and then deletes the directory itself.

        Args:
            directory_path (str): The path to the directory to be deleted.

        Returns:
            str: A success message if the operation is completed successfully.
        """
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            # Remove all contents inside the directory
            shutil.rmtree(directory_path)
            return f"Directory '{directory_path}' and all its contents have been deleted successfully."
        else:
            return f"Directory '{directory_path}' does not exist."
        

    def chat(self, message, history):
        """
        Main chat function handling Slack messages, RAG, and fallback logic.
        """

         
        ICON_URL = "https://raw.githubusercontent.com/gitpranjal/SlackAssistant/main/static/slack_bot.png"
        ICON_HTML = f'<img src="{ICON_URL}" alt="icon" style="width:35px; height:30px;">'


        # Handle clear data request
        if self._is_clear_history_request(message):
            gr.update(history=[])
            self.rag_handler.reset_vectorstore_data()
            self.delete_directory_with_files("knowledge_base")
            return [{"role": "assistant", "content": f"{ICON_HTML} History and data cleared successfully."}]
        
        if self._is_describe_request(message):

            print("User requested to describe a slack channel")
            channel_name = self.extract_channel_name(message)
            if not channel_name:
                return [{"role": "assistant", "content": f"{ICON_HTML} Unable to fetch or analyze Slack channel '#{channel_name}'."}]
            
            channels = self.slack_manager.list_channels()
            channel_names_list = set([channel["name"] for channel in channels])
            if channel_name not in channel_names_list:
                return [{"role": "assistant", "content": f"{ICON_HTML} Slack channel with name'#{channel_name}' not present in the current workspace or is hidden somehow."}]
            
            channel_file_path = f"knowledge_base/{channel_name}_messages.txt"

            _, channel_description = self.slack_manager.get_channel_id_description_by_name(channel_name)

            complete_channel_info = "Channel Description: "+channel_description+"\n"+"Conversations: \n"

            if os.path.exists(channel_file_path):
                with open(channel_file_path, "r", encoding="utf-8") as file:
                    for line in file:
                        complete_channel_info += line


            payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": f"""You are a helpful assistant that helps respond by describing any slack channel that belongs to the current workspace.
                          Give a detailed summary, description of the channel based upon given information. Mention the given information down below in response.
                           The first line is a short description and the rest, if given, is conversation on that channel. If no information about the conversation in the channel is present, mention that and ask the user 
                          to first analyze the channel using 'analyze slack channel #{channel_name}'. Don't hallucinate. If you do't have enough description, say so. Here's the given information:
                           Complete Channel Info -> {complete_channel_info} """}] + history + [{"role": "user", "content": message}],
            "stream": False
          }
            
            response = requests.post(self.localAPIUrl, json=payload, headers=self.header)
            if response.status_code == 200:
                llm_response = response.json().get("message", {}).get("content", "")
                return [{"role": "assistant", "content": f"{ICON_HTML} {llm_response}"}]
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")


            

        
        if self._is_slack_channel_listing_request(message):

            print("User requested to list out slack channels")

            channels =self.slack_manager.list_channels()
            if not channels:
                return "No channel found. Channel list is empty"
            
            payload = {
            "model": self.model,
            "messages": [{
                "role": "system",
                "content": f"""You are a helpful assistant that helps in finding information about Slack channels. 
                The user message will ask something like "find out relevant channels related to this 'topic'. Use your intelligence, analyze the user message and help them get,
                filtering out the Slack channels from the given list of channels that might be related to what the user is referring to. 
                If the user message doesn't mention any relevant topic, respond by listing out all the channels. 
                Here's a list of Slack channels with their descriptions: 
                {"; ".join(["Name: " + channel["name"] + ", Description: " + channel["purpose"]["value"] for channel in channels])}
                """
            }] + history + [{"role": "user", "content": message}],
            "stream": False
        }

            
            response = requests.post(self.localAPIUrl, json=payload, headers=self.header)
            if response.status_code == 200:
                llm_response = response.json().get("message", {}).get("content", "")
                return [{"role": "assistant", "content": f"{ICON_HTML} {llm_response}"}]
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")
            


        # Handle Slack channel analysis
        if self._is_slack_channel_request(message):
            channel_name = self.extract_channel_name(message)
            channels =self.slack_manager.list_channels()
            channels = set([channel["name"] for channel in channels])
            if channel_name not in channels:
                return [{"role": "assistant", "content": f"{ICON_HTML} Channel name not recognized in current workspace. Please specify a valid Slack channel name using '#channel_name'."}]

            if channel_name:
                self.slack_manager.fetch_channel_messages(channel_name)
                slack_file_path = f"knowledge_base/{channel_name}_messages.txt"
                if os.path.exists(slack_file_path):
                    self.rag_handler.update_vectorstore_from_file(slack_file_path)
                    return [{"role": "assistant", "content": f"{ICON_HTML} Slack channel '#{channel_name}' has been analyzed and added to the knowledge base."}]
                else:
                    return [{"role": "assistant", "content": f"{ICON_HTML} Unable to fetch or analyze Slack channel '#{channel_name}'."}]
            else:
                return [{"role": "assistant", "content": f"{ICON_HTML} Please specify a valid Slack channel name using '#channel_name'."}]

        # RAG response
        rag_response = self.rag_handler.chat(message).strip()
        if rag_response != "NIL":
            return [{"role": "assistant", "content": f"{ICON_HTML} {rag_response}"}]

        # Fallback to LLM
        print("Falling back to LLM response")
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": "You are a helpful assistant. You are fall back right now because the rag handler object couldn't fetch anything relevant from vectorstore. You're not responsing anthing from the slack channels in current workspace. Specify this fact in your response and after specfying, respond with your intelligence."}] + history + [{"role": "user", "content": message}],
            "stream": False
        }
        response = requests.post(self.localAPIUrl, json=payload, headers=self.header)
        if response.status_code == 200:
            llm_response = response.json().get("message", {}).get("content", "")
            return [{"role": "assistant", "content": f"{ICON_HTML} {llm_response}"}]
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
