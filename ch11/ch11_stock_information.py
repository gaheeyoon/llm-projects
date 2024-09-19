##### 기본 정보 입력 #####
# 스트림릿 패키지 추가
import streamlit as st
# OpenAI 패키지 추가
import openai
# assistant 상태 및 출력 파일 정리를 위한 패키지 추가
import time
import json
# 종목 정보 호출을 위한 yfinance 패키지 추가
import yfinance as yf

# OpenAI API 키 불러오기
OPENAI_API_KEY = "여기에 API 키를 넣어주세요"
# assistant ID 불러오기
ASSISTANT_ID = "assistant id 입력"

##### 기능 구현 함수 #####
def get_stock_price(symbol):
    stock = yf.Ticker(symbol)
    price = stock.info['currentPrice']
    return price

def get_latest_company_news(symbol):
    stock = yf.Ticker(symbol)
    news = stock.news
    # 최신 뉴스 3개를 리스트에 저장
    news_list = []
    num =1
    for item in news[:3]:
        news_list.append(f"{num}: title : "+item['title']+", publisher:"+item['publisher']+", link :"+item['link'])
        num+=1
    return news_list

def requires_actions(client, run):
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    tools_output_array = []
    for each_tool in tools_to_call:
        tool_call_id = each_tool.id
        function_name = each_tool.function.name
        function_arg = each_tool.function.arguments
        # Json 포맷팅
        function_arg = json.loads(each_tool.function.arguments)
        if (function_name == 'get_stock_price'):
            ## 주가 정보 저장 ##
            output=get_stock_price(function_arg["symbol"])
        if (function_name == 'get_latest_company_news'):
            ## 최신 뉴스 정보 저장 ##
            output=get_latest_company_news(function_arg["symbol"])

        tools_output_array.append({"tool_call_id": tool_call_id, "output": json.dumps(output)})
    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id = st.session_state.Thread.id,
        run_id = run.id,
        tool_outputs=tools_output_array)
    while run.status not in ["completed", "failed","requires_action"]:
        run = client.beta.threads.runs.retrieve(
            thread_id= st.session_state.Thread.id,
            run_id= run.id)
        time.sleep(2)
    return run

def get_response(client, run):
    if run.status == "queued":
        while run.status not in ["completed", "failed", "requires_action"]:
            run = client.beta.threads.runs.retrieve(
            thread_id= st.session_state.Thread.id,
            run_id= run.id)
            time.sleep(2)
        response = get_response(client, run)
    elif run.status =="requires_action":
        run = requires_actions(client, run)
        response = get_response(client, run)
    elif run.status =="completed":
        messages = client.beta.threads.messages.list(thread_id=st.session_state.Thread.id)
        response = messages.data[0].content[0].text.value
    else:
        response = "문제가 발생했습니다. 다시 질문해주세요"
    return response

##### 메인 함수 #####
def main():
    st.set_page_config(page_title="주가 정보 AI 챗봇")
    
    # session state 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "Thread" not in st.session_state:
        st.session_state.Thread = None
    
    # 사이드바
    with st.sidebar:
        # 대화 초기화
        st.write("대화 초기화 버튼")
        reset_button = st.button("Reset")
        if reset_button:
            st.session_state.messages = []
            st.session_state.Thread = None
    
    st.header("📈주가 정보 AI 챗봇")
    st.markdown('---')
    
    # 기존 대화 내용을 화면에 채팅 형식으로 구현
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # OpenAI 클라이언트 생성 및 assistant 불러오기
    client = openai.OpenAI(api_key = OPENAI_API_KEY)
    assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
    
    # Thread 생성하기
    if st.session_state.Thread == None:
        st.session_state.Thread = client.beta.threads.create()
    
    # 채팅을 입력받고 답변을 생성
    if prompt := st.chat_input("조회를 원하는 종목을 말씀하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        message = client.beta.threads.messages.create(
            thread_id=st.session_state.Thread.id,
            role="user",
            content=prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
    
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.Thread.id,
                    assistant_id=assistant.id)
                response = get_response(client, run)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == '__main__':
    main()