
from crewai.tools import BaseTool
from pydantic import Field
import os
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Type
from helper import load_env, get_supabase_url, get_supabase_key
load_env()


url: str = os.getenv("SUPERBASE_URL")
key: str = os.getenv("SUPERBASE_KEY")
supabase: Client = create_client(url, key)

class SupabaseDeleteRowInputTool(BaseModel):
    table_name: str = Field(..., description="String containing the table name.")
    column_name: str = Field(..., description="String containing the column name.")
    value: str = Field(..., description="String containing the value.")

class SupabaseDeleteRowTool(BaseTool):
    name: str = "Supabase Delete Row Tool"
    description: str = "This tool is useful for deleting a row from the Supabase database."
    
    args_schema: Type[BaseModel] = SupabaseDeleteRowInputTool

    def _run(self, table_name: str, column_name: str, value: str) -> str:
        result = supabase.table(table_name).delete().eq(column_name, value).execute()
        return result
