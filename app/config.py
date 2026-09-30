import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    #get our api keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "fda-drug-labels")
    # verify if any variable is messing 
    def validate(self):

        missing = []
        if not self.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY")
        if not self.PINECONE_API_KEY:
            missing.append("PINECONE_API_KEY")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please check your .env file."
            )

settings =Settings()