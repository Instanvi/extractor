from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time
import logging


class DataHandler:
    def __init__(self, 
                client,
                database_name: str,
                collection_name: str):
        """
        Initialize the data inserter.
        
        Args:
            client: client connection to db
            database_name: Name of the database
            collection_name: Name of the collection
        """

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('MongoDataHandler')


        self.client = client
        self.collection_name = collection_name
        self.db = self.client[database_name]

        # Ensure collection exists
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(collection_name)
        
        self.collection = self.db[collection_name]
        
        self.logger.info(f"Connected to DB: {self.db} and Collection: {self.collection_name} ")
    
    def insert_document(self, document) -> Optional[str]:
        """
            Insert a single document into MongoDB Atlas and return its ID.
        """
        try:
            
            # Insert the document
            result = self.collection.insert_one(document)
            
            # Get the inserted document's ID
            document_id = str(result.inserted_id)
            return document_id
            
        except Exception as e:
            self.logger.error(f"Error inserting documents: {str(e)}")
            return None