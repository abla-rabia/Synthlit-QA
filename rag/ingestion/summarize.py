from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


def separate_content(chunk):
    content_chunk=[
        "type":"", 
        "raw_text":chunk.text, 
        "images":[], 
        "tables":[]
    ]
    # and we loop over the chunk content metadata.orig_elements and saved them in the content chunk , and we get the type, 
def summarise_chunks(chunks):
    #Preparing the VLM that is going to summarise
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0
    )
    #The list of the enhanced chunks (langchain document)
    for i, chunk in chunks : 
        chunk_content=separate_content(chunk)

        if chunk_content.tables or chunk_content.images: 
            prompt=""""""
            result=llm.invoke(prompt).content
            enhanced.text_page=result
            enhanced.metadata={"type":'text', "raw_text":chunk.content, "raw_image":chunk_content.images, "raw_tables":chunk_content.tables}

        else:
            enhanced.text_page=chunk.content
            enhanced.metadata={"type":'text', "raw_text":chunk.content}
        enhanced_chunks.append(enhanced)
        
    enhanced_chunks=[]
