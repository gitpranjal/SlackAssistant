import os
import requests
import time
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from chromadb.config import Settings
from RAG.embedding import SentenceTransformerEmbeddings

class RAGHandler:
    def __init__(self, **kwargs):
        self.model_url = kwargs.get("model_url", "http://localhost:11434/api/chat")
        self.system_message = kwargs.get("system_message", """You are a helpful RAG assistant. 
                                         Use retrieval-augmented generation only if the user message is relevant to anything stored in vectorstore. Don't hallucinate. 
                                         Return string 'NIL' if the user message is not related to the retrieved documents or the retrieved document is dummy document with file_name dummy.txt.""")
        self.db_name = kwargs.get("db_name", "developer_assistant_vectorstore")
        self.vectorstore = None

        self.initialize_vectorstore()

    def initialize_vectorstore(self):
        """
        Initialize the vector store with a dummy document if it doesn't exist.
        """
        dummy_document = {
            "page_content": "This is a dummy document for initialization purposes.",
            "metadata": {"file_name": "dummy.txt", "file_path": "/dummy/path", "doc_type": "txt"}
        }

        embedding_model = SentenceTransformerEmbeddings("sentence-transformers/all-MiniLM-L6-v2")
        retry_attempts = 3

        if not os.path.exists(self.db_name):
            for attempt in range(retry_attempts):
                try:
                    dummy_chunk = Document(page_content=dummy_document["page_content"], metadata=dummy_document["metadata"])
                    self.vectorstore = Chroma.from_documents(
                        documents=[dummy_chunk],
                        embedding=embedding_model,
                        persist_directory=self.db_name
                    )
                    print(f"Vectorstore initialized with a dummy document at {os.path.abspath(self.vectorstore._persist_directory)}")
                    os.system(f"chmod -R u+w {os.path.abspath(self.vectorstore._persist_directory)}")
                    break
                except Exception as e:
                    if attempt < retry_attempts - 1:
                        print(f"Retrying vectorstore initialization... Attempt {attempt + 1}")
                        time.sleep(2)
                    else:
                        print(f"Failed to initialize vectorstore after {retry_attempts} attempts. Error: {e}")
        else:
            embedding_model = SentenceTransformerEmbeddings("sentence-transformers/all-MiniLM-L6-v2")
            self.vectorstore = Chroma(embedding_function=embedding_model, persist_directory=self.db_name)
            print("Vectorstore loaded successfully.")

    def update_vectorstore(self, channel_name, slack_messages):
        """
        Updates the vectorstore with Slack channel messages.
        """
        documents = []

        for message in slack_messages:
            text = message.get('text', 'No text')
            user = message.get('user', 'Unknown')
            metadata = {
                "user": user,
                "channel": channel_name,
                "timestamp": message.get('ts', 'Unknown')
            }
            documents.append(Document(page_content=text, metadata=metadata))

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)

        if not os.path.exists(self.db_name):
            self.initialize_vectorstore()

        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        self.vectorstore.add_texts(texts=texts, metadatas=metadatas)
        print(f"Added {len(texts)} messages to the vectorstore from channel '{channel_name}'.")

    def update_vectorstore_from_file(self, slack_file_path):
        """
        Updates the vectorstore by reading Slack messages from a file.
        """
        if not os.path.exists(slack_file_path):
            print(f"File {slack_file_path} does not exist.")
            return

        channel_name = os.path.basename(slack_file_path).replace("_messages.txt", "")
        slack_messages = []

        try:
            with open(slack_file_path, "r", encoding="utf-8") as file:
                for line in file:
                    parts = line.split(", Text: ")
                    if len(parts) == 2:
                        user = parts[0].replace("User: ", "").strip()
                        text = parts[1].strip()
                        slack_messages.append({"user": user, "text": text})
        except Exception as e:
            print(f"Error reading Slack messages from file: {e}")
            return

        self.update_vectorstore(channel_name, slack_messages)

    def reset_vectorstore_data(self):
        """
        Clear all data from the Chroma vector store and add dummy data.
        """
        try:
            # List existing collections
            collections = self.vectorstore._client.list_collections()
            print("List of collections in vectorstore:", collections)

            # Check if the vector store has a collection
            if self.vectorstore._collection:
                collection_name = self.vectorstore._collection.name
                print(f"Clearing all vectors from the collection: {collection_name}")

                # Retrieve all vector IDs
                all_vectors = self.vectorstore._collection.get()  # Fetch all vectors without a filter
                vector_ids = all_vectors.get("ids", [])

                if vector_ids:
                    self.vectorstore._collection.delete(ids=vector_ids)
                    print(f"All vectors deleted from the collection: {collection_name}")
                else:
                    print("No vectors found in the collection to delete.")
            else:
                print("No collection found in the vector store.")

            # Add dummy data to the vectorstore
            dummy_texts = ["This is a dummy document.", "Another dummy document."]
            dummy_metadatas = [{"source": "dummy1"}, {"source": "dummy2"}]

            print("Adding dummy data to the vectorstore...")
            self.vectorstore.add_texts(texts=dummy_texts, metadatas=dummy_metadatas)
            print("Dummy data added successfully.")

        except Exception as e:
            print(f"Error resetting vector store: {e}")

    def retrieve_documents(self, query):
        """
        Retrieve relevant documents from the vectorstore using the query.
        """
        if not self.vectorstore:
            return []
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        return retriever.get_relevant_documents(query)

    def generate_response(self, query, retrieved_documents):
        """
        Generate a response using the LLM with retrieved documents as context.
        """
        context = "\n\n".join([doc.page_content for doc in retrieved_documents])
        prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"

        payload = {
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        response = requests.post(self.model_url, json=payload)
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "No content returned.")
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def chat(self, message):
        """
        Unified chat function for general queries and RAG-based responses.
        """
        if self.vectorstore:
            retrieved_docs = self.retrieve_documents(message)
            if retrieved_docs:
                return self.generate_response(message, retrieved_docs)
            return "No relevant documents found."

        return "Vectorstore not initialized."
