import os
from dotenv import load_dotenv, find_dotenv
import os


# these expect to find a .env file at the directory above the lesson.                                                                                                                     # the format for that file is (without the comment)                                                                                                                                       #API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService                                                                                                                                     
def load_env():
    _ = load_dotenv(find_dotenv())

def get_openai_api_key():
    load_env()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return openai_api_key

def get_supabase_url():
    load_env()
    supabase_url = os.getenv("SUPERBASE_URL")
    return supabase_url

def get_supabase_key():
    load_env()
    supabase_key = os.getenv("SUPERBASE_KEY")
    return supabase_key