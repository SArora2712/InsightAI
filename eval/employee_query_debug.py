from agents.orchestrator.synthesizer import synthesize_final_answer
from agents.sql_agent.generator import run_sql_agent

sql_result = run_sql_agent("How balanced is revenue across our top sales employees?")
print("SQL generated:", sql_result["sql"])
print()

result = synthesize_final_answer(
    "How balanced is revenue across our top sales employees?",
    rag_result=None, sql_result=sql_result, web_result=None,
)
print("Final answer:", result["answer"])