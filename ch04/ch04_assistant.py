##### 기본 정보 입력 ####
# 음성 녹음을 위한 오디오 레코더 패키지 추가
from audiorecorder import audiorecorder

# 스트림릿 패키지 추가
import streamlit as st

# OpenAI 패키지 추가
from openai import OpenAI

# 파이썬 기본 패키지
import os
import base64
import numpy as np

##### 기능 구현 함수 #####
# 음성을 텍스트로 변환하는 STT(Speech-to-Text) API
def STT(audio, client):
    # Whisper API가 파일 형태로 음성을 입력받으므로 input.mp3 파일을 저장
    filename='input.mp3'
    wav_file = open(filename, "wb")
    wav_file.write(audio.export().read())
    wav_file.close()

    # 음성 파일 열기
    audio_file = open(filename, "rb")
    # Whisper 모델을 활용하여 텍스트 얻기
    try:
        # openai의 Whisper API 를 활용하여 텍스트를 추출합니다.
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    
        # Whisper로 TTS가 끝났으니 이제 mp3 파일을 다시 삭제합니다.
        audio_file.close()
        os.remove(filename)
    except:
        transcript='API Key를 확인해주세요'
    return transcript

# 텍스트를 음성으로 변환하는 TTS(Text-to-Speech) API
def TTS(response, client):
    # TTS를 활용하여 만든 음성을 파일로 저장
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="onyx",
        input=response,
    ) as response:
        filename ="output.mp3"
        response.stream_to_file(filename)

    # 저장한 음성 파일을 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()

        # 스트림릿에서 음성 자동 재생
        md = f'''
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        '''
        st.markdown(md, unsafe_allow_html=True,)
    # 폴더에 남지 않도록 파일을 삭제
    os.remove(filename)

# 음성 비서의 답변을 생성하는 ChatGPT API
def ask_gpt(prompt, client):
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=prompt
    )
    return response.choices[0].message.content

##### 메인 함수#####
def main():
    # OpenAI API 키 지정하기
    client = OpenAI(api_key="여기에 API 키를 넣어주세요")
    
    # 화면 상단에 표시될 프로그램의 이름
    st.set_page_config(
        page_title="음성 비서 프로그램🔊",
        layout="wide")
    
    # st.session_state["check_audio"]: 프로그램이 재실행될 때마다 이전 녹음 파일 정보가 버퍼에 남아있어 실행되는 것을 방지하기 위해 이전 녹음 파일 정보를 저장합니다.
    if "check_audio" not in st.session_state:
        st.session_state["check_audio"] = []
    
    # st.session_state["messages"]: GPT API에 입력으로 들어갈 프롬프트 양식. 이전 질문 및 답변을 누적하여 저장.
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": 'You are a thoughtful assistant. Respond to all input in 25 words and answer in korean'}]
    
    # 기능 구현 공간
    col1, col2 = st.columns(2)
    
    # 왼쪽 공간 작성
    with col1:
        # 제목
        st.header('AI Assistant 🔊')
        st.image('ai.png', width=200)
        # 구분선
        st.markdown('---')
    
        # 음성 입력 확인용 플래그
        flag_start = False
    
        # 음성 녹음 아이콘 추가
        audio = audiorecorder("질문", "녹음중...")
        if len(audio) > 0 and not np.array_equal(audio, st.session_state["check_audio"]):
            # 음성 재생
            st.audio(audio.export().read())
        
            # 음원 파일에서 텍스트를 추출
            question = STT(audio, client)
            
            # GPT 모델에 넣을 프롬프트를 위해 질문을 저장. 이때 기존 내용을 누적.
            st.session_state["messages"] = st.session_state["messages"]+ [{"role": "user", "content": question}]
            # audio 버퍼 확인을 위해 현 시점의 오디오 정보를 저장
            st.session_state["check_audio"] = audio
            flag_start=True
    
    # 오른쪽 공간 작성
    with col2:
        st.subheader('대화기록 ⌨')
        if flag_start:
        
            # ChatGPT에게 답변 얻기
            response = ask_gpt(st.session_state["messages"], client)
        
            # GPT 모델에 넣을 프롬프트를 위해 답변 내용을 저장
            st.session_state["messages"] = st.session_state["messages"]+ [{"role": "assistant", "content": response}]
        
            # User와 Assistant의 대화를 화면에 출력. 단, 시스템 프롬프트는 제외
            for message in st.session_state["messages"]:
                if message["role"] != 'system':
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
        
            # TTS를 활용하여 음성 파일 생성 및 재생
            TTS(response, client)

if __name__=="__main__":
    main()