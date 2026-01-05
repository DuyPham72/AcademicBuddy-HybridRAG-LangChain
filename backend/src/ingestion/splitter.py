from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

def split_documents(documents):
    '''
    Split the Markdown result into multiple chunk base on its header
    '''
    headers_to_split_on = [("#", "Title"), ("##", "Section"), ("###", "Subsection")]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    # Split by word if the chunk is too long
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, length_function=len
    )
    
    final_chunks = []
    for doc in documents:
        # Split markdown headers
        splits = markdown_splitter.split_text(doc.page_content)

        # Copy metadata to splits
        for split in splits:
            split.metadata.update(doc.metadata)
            
        # Split by char
        char_splits = text_splitter.split_documents(splits)
        final_chunks.extend(char_splits)
    
    return final_chunks