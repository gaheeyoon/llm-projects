from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
script = "요약을 원하는 장문의 텍스트"

# 요약을 위한 랭체인의 ChatGPT 세팅
llm = ChatOpenAI(temperature=0,
                 openai_api_key="여기에 API 키를 넣어주세요",
                 max_tokens=4000,
                 model_name="gpt-3.5-turbo",
                 request_timeout=120
)

# 프롬프트 설정
prompt = PromptTemplate(
    template="""백틱으로 둘러싸인 전사본을 이용해 해당 텍스트를 요약해주세요. \
        ```{text}``` 단, 영어로 작성해주세요.
        """, input_variables=["text"]
)
combine_prompt = PromptTemplate(
    template="""백틱으로 둘러싸인 유튜브 스크립트를 모두 조합하여 \
        ```{text}```
        10문장 내외의 간결한 요약문을 제공해주세요. 단, 영어로 작성해주세요.
        """, input_variables=["text"]
)

# 랭체인을 활용하여 긴 글 요약
# 글 쪼개기
text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=0)
texts = text_splitter.create_documents([script])

# 요약하기
chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=False,
                             map_prompt=prompt, combine_prompt=combine_prompt)
summerize = chain.invoke(texts)["output_text"]

# 최종 출력
print(summerize)