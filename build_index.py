#call function from index_builder


from app.rag.index_builder import build_all_indexes

if __name__ == "__main__":
    build_all_indexes(reset=True)

    