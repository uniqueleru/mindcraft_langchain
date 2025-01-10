from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import logging

def search_vector_db(
    db_directory: str = "./minecraft_knowledge/vector_database/public_knowledge",
    query_llm = "gpt-4o-mini",
    temperature: float = 0,
    goal: str = "build a nether portal",
    stat: str =
    """
    STATS
    - Position: x: 33.64, y: 66.00, z: -5.50
    - Gamemode: survival
    - Health: 20 / 20
    - Hunger: 20 / 20
    - Biome: forest
    - Weather: Clear
    - Block Below: oak_leaves
    - Block at Legs: air
    - Block at Head: air
    - First Solid Block Above Head: none
    - Time: Afternoon- Current Action: Idle
    - Nearby Human Players: None.
    - Nearby Bot Players: None.
    INVENTORY
    - oak_sapling: 4
    - oak_log: 7
    WEARING: Nothing
    """
                     
):
    load_dotenv()
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    db = Chroma(
        embedding_function=embeddings,
        persist_directory=db_directory
    )
    llm = ChatOpenAI(model=query_llm,temperature=temperature)
    retriever_from_llm = MultiQueryRetriever.from_llm(
        retriever=db.as_retriever(),
        llm=llm
    )
    logging.basicConfig()
    logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
    unique_docs = retriever_from_llm.invoke(input=goal+"\n"+stat)
    print(len(unique_docs))
    return unique_docs

if __name__ == "__main__":
    print(search_vector_db())