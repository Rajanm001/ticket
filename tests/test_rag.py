from app.rag import Retriever


def test_retriever_returns_list() -> None:
    retriever = Retriever()
    results = retriever.retrieve("refund delayed")
    assert isinstance(results, list)
