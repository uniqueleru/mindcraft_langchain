import os
import glob
import hashlib
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

def get_file_hash(filepath):
    """파일의 SHA-256 해시 값을 반환합니다."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as file:
        while True:
            chunk = file.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def create_vector_db(
    source_dir: str = "./minecraft_knowledge/original_src",
    persist_directory: str = "./minecraft_knowledge/vector_database/public_knowledge",
    collection_name: str = "minecraft_knowledge",
    chunk_size: int = 500,
    chunk_overlap: int = 200
):

    load_dotenv()
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    vectordb = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

    existing_collections = [col.name for col in vectordb._client.list_collections()]
    if collection_name not in existing_collections:
        print(f"컬렉션 '{collection_name}'이 없습니다. 새로 생성합니다.")
        collection = vectordb._client.create_collection(name=collection_name)
    else:
        print(f"컬렉션 '{collection_name}'이 이미 존재합니다. 해당 컬렉션에 문서를 추가/갱신합니다.")
        collection = vectordb._client.get_collection(name=collection_name)

    for filepath in glob.glob(os.path.join(source_dir, "*")):
        file_ext = os.path.splitext(filepath)[1].lower()
        if file_ext == ".pdf":
            loader = PyPDFLoader(filepath)
        elif file_ext == ".docx":
            loader = UnstructuredWordDocumentLoader(filepath)
        elif file_ext == ".txt":
            loader = TextLoader(filepath)
        else:
            print(f"지원하지 않는 파일 형식입니다: {filepath}")
            continue

        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        splitted_docs = text_splitter.split_documents(docs)

        file_hash = get_file_hash(filepath)
        filename = os.path.splitext(os.path.basename(filepath))[0]


        existing_ids = collection.get(where={"filename": filename})['ids']
        if existing_ids:

            existing_hashes = collection.get(ids=existing_ids, include=["metadatas"])['metadatas']
            existing_hashes = [meta.get('file_hash') for meta in existing_hashes if meta.get('file_hash')]

            if not existing_hashes or file_hash not in existing_hashes:
                print(f"파일 '{filename}'이 변경되었습니다. 이전 데이터를 삭제하고 다시 임베딩합니다.")
                collection.delete(ids=existing_ids)
            else:
                print(f"파일 '{filename}'은 변경되지 않았습니다. 임베딩을 건너뜁니다.")
                continue

        for i, doc in enumerate(splitted_docs):
            doc_id = f"{filename}_{i}"
            doc.metadata["file_hash"] = file_hash
            doc.metadata["filename"] = filename

            collection.add(
                documents=[doc.page_content],
                metadatas=[doc.metadata],
                ids=[doc_id]
            )

    print(f"벡터 DB가 '{persist_directory}' 경로에 성공적으로 저장/갱신되었습니다.")

    return vectordb

if __name__ == "__main__":
    create_vector_db(
        chunk_size=500,
        chunk_overlap=200
    )