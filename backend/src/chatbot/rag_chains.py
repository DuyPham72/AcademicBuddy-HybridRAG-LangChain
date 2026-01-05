from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.chatbot.client import get_llm
from src.utils import load_prompts

PROMPTS = load_prompts()

def get_chat_chain():
    """
    Chain for answering questions based on context.
    """
    llm = get_llm(streaming=True)
    
    system_prompt = PROMPTS["rag_system_prompt"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])
    
    return prompt | llm | StrOutputParser()

def get_query_transform_chain():
    """
    Chain for rewriting follow-up questions into standalone queries.
    """
    llm = get_llm(streaming=False) 
    
    system_prompt = PROMPTS["query_rewrite_prompt"]
    examples = PROMPTS["query_transform_examples"]

    example_prompt = ChatPromptTemplate.from_messages([
        ("human", "{input}"), 
        ("ai", "{output}")
    ])
    
    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt, 
        examples=examples
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        few_shot_prompt,
        ("human", "{input}"),
    ])
    
    return prompt | llm | StrOutputParser()