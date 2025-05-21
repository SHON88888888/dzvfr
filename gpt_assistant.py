# gpt_assistant.py
from openai import OpenAI
from dotenv import load_dotenv
import os
import textwrap

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Генерация ответа с учётом контекста и истории диалога
def answer_question_with_context(question, vector_store, chat_history):
    # Ищем релевантные фрагменты
    docs = vector_store.similarity_search(question, k=4)
    context = "\n---\n".join([f"[{d.metadata['source']}]\n{d.page_content}" for d in docs])

    system_prompt = f"""
    Ты — экспертный нейро-ассистент для аудитора.
    Ты отвечаешь на вопросы строго по тексту аудиторских отчётов и регламентов.
    Если вопрос не связан с содержанием — вежливо отказываешься отвечать.
    
    Вот выдержки из документов:
    """
    {textwrap.shorten(context, width=4000)}
    """
    """

    messages = [
        {"role": "system", "content": system_prompt},
        *chat_history,
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    return response.choices[0].message.content.strip()
