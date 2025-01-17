import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

class SlackBotManager:
    def __init__(self):
        """
        Initialize the SlackBotManager with a WebClient instance.
        """
        load_dotenv()  # Load environment variables from .env
        self.token = os.getenv("SLACK_TOKEN")
        if not self.token:
            raise ValueError("SLACK_TOKEN is not set in the .env file.")
        self.client = WebClient(token=self.token)
        self.bot_user_id, self.bot_name = self.get_bot_user_details()

    def get_bot_user_details(self):
        """
        Fetch and return the bot's user ID and name.
        """
        try:
            response = self.client.auth_test()
            bot_user_id = response["user_id"]
            bot_name = response.get("user", "Unknown")
            print(f"Bot User ID: {bot_user_id}, Bot Name: {bot_name}")
            return bot_user_id, bot_name
        except SlackApiError as e:
            raise Exception(f"Error fetching bot user details: {e.response['error']}")

    def list_channels(self, types="public_channel,private_channel"):
        """
        List all channels (public and private).
        """
        try:
            response = self.client.conversations_list(types=types, limit=1000)
            channels = response.get("channels", [])
            for channel in channels:
                print(f"Channel Name: {channel['name']}, Channel ID: {channel['id']}")
                print(channel["purpose"]["value"])
            return channels
        except SlackApiError as e:
            print(f"Error fetching channels: {e.response['error']}")
            return []

    def get_channel_id_description_by_name(self, channel_name):
        """
        Get a channel's ID by its name.
        """
        channels = self.list_channels()
        for channel in channels:
            if channel["name"] == channel_name:
                return channel["id"], channel["purpose"]["value"]
        print(f"Channel '{channel_name}' not found.")
        return None

    def invite_bot_to_channel(self, channel_id):
        """
        Invite the bot to a public or private channel.
        """
        try:
            self.client.conversations_join(channel=channel_id)
            print(f"Bot joined the channel: {channel_id}")
        except SlackApiError as e:
            if e.response['error'] == 'already_in_channel':
                print(f"Bot is already in the channel: {channel_id}")
            elif e.response['error'] == 'not_in_channel':
                print(f"Error: Bot needs to be explicitly invited to the private channel: {channel_id}")
            else:
                print(f"Error joining channel: {e.response['error']}")

    def fetch_channel_messages(self, channel_name):
        """
        Fetch and save all messages from a public or private channel to a text file.
        """
        channel_id, channel_description = self.get_channel_id_description_by_name(channel_name)
        if not channel_id:
            return

        try:
            messages = []
            next_cursor = None

            while True:
                response = self.client.conversations_history(
                    channel=channel_id, cursor=next_cursor, limit=100
                )
                messages.extend(response['messages'])

                # Check if there's a next page
                next_cursor = response.get('response_metadata', {}).get('next_cursor')
                if not next_cursor:
                    break

            directory_path = "knowledge_base"
            os.makedirs(directory_path, exist_ok=True)
            print(f"Directory '{directory_path}' is ready.")

            # Write messages to a text file
            file_name = f"knowledge_base/{channel_name}_messages.txt"
            with open(file_name, "w", encoding="utf-8") as file:
                for msg in messages[::-1]:
                    user = msg.get('user', 'Unknown')
                    text = msg.get('text', 'No text')
                    file.write(f"User: {user}, Text: {text}\n")
            print(f"Messages saved to {file_name}")

        except SlackApiError as e:
            if e.response['error'] == 'not_in_channel':
                print(f"Bot is not in the channel '{channel_name}'. Attempting to add bot...")
                try:
                    self.invite_bot_to_channel(channel_id)
                    print("Bot successfully added. Retrying to fetch messages...")
                    self.fetch_channel_messages(channel_name)  # Retry fetching messages
                except Exception as invite_error:
                    print(f"Failed to add bot to the channel '{channel_name}': {invite_error}")
            else:
                print(f"Error fetching messages: {e.response['error']}")

