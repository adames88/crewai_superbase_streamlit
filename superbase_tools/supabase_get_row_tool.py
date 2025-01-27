from crewai.tools import BaseTool
import os
from supabase import create_client, Client
from helper import load_env, get_supabase_url, get_supabase_key
load_env()


url: str = os.getenv("SUPERBASE_URL")
key: str = os.getenv("SUPERBASE_KEY")
supabase: Client = create_client(url, key)

class SupabaseGetRowTool(BaseTool):
    name: str = "Supabase Get Row Tool"
    description: str = "This tool is useful for getting a row from the Supabase database."

    def _run(self, table_name: str, column_name: str, value: str) -> str:
        result = supabase.table(table_name).select("*").eq(column_name, value).execute()
        return result