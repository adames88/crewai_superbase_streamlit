from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)

txt = open("knowledge/table_info.txt", "r").read()

print(txt)