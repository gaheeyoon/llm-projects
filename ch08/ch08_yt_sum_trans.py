##### 기본 정보 입력 #####
# 스트림릿 패키지 추가
import streamlit as st

# OpenAI 패키지 추가
import openai

# 유튜브 영상을 다운로드하기 위한 pytubefix 패키지 추가
from pytubefix import YouTube

# 유튜브 영상을 번역, 요약하기 위한 랭체인 패키지 추가
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI

# 기타 필요한 기본 패키지 추가
import re
import os
import shutil

# Whisper를 사용하기 위해 client 선언
api_key = "여기에 API 키를 넣어주세요"
client = openai.OpenAI(
    api_key=api_key
)

##### 기능 구현 함수 정리 #####
# 주소를 입력받아 유튜브 동영상의 음성(mp3)을 추출하는 함수
def get_audio(url):
    yt = YouTube(url)
    audio = yt.streams.filter(only_audio=True).first()
    audio_file = audio.download(output_path=".")
    base, ext = os.path.splitext(audio_file)
    new_audio_file = base + ".mp3"
    shutil.move(audio_file, new_audio_file)
    return new_audio_file

# 음성 파일 주소를 전달받아 스크립트를 추출하는 함수
def get_transcribe(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            response_format="text",
            file=audio_file
        )
    return transcript

# 영어 입력이 들어오면 한글로 번역 및 불릿 포인트 요약을 수행
def trans(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 영한 번역가이자 요약가입니다. 들어오는 모든 입력을 한국어로 번역하고 불릿 포인트를 이용해 요약해주세요. 반드시 불릿 포인트로 요약해야 합니다."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

# 유튜브 주소의 형태를 정규 표현식(Regex)으로 체크하는 함수
def youtube_url_check(url):
    pattern = r'^https:\/\/www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)(\&ab_channel=[\w\d]+)?$'
    match = re.match(pattern, url)
    return match is not None

##### 메인 함수 #####
def main():
    # session state 초기화
    if "summarize" not in st.session_state:
        st.session_state["summarize"] = ""

    # 메인 공간
    st.header("📽 YouTube Summarizer")
    st.image("ai.png", width=200)
    youtube_video_url = st.text_input("Please write down the YouTube address.", placeholder="https://www.youtube.com/watch?v=**********")
    st.markdown("---")

    # URL이 입력됐을 경우
    if len(youtube_video_url) > 2:
        # URL을 잘못 입력했을 경우
        if not youtube_url_check(youtube_video_url):
            st.error("Youtube URL을 확인하세요.")
        # URL을 제대로 입력했을 경우
        else:
            # 동영상 재생 화면 불러오기
            width = 50
            side = width / 2
            _, container, _ = st.columns([side, width, side])
            container.video(data=youtube_video_url)

            # 영상 속 자막 추출하기
            audio_file = get_audio(youtube_video_url)
            transcript = get_transcribe(audio_file)

            st.subheader("Summary Outcome (in English)")
            # 언어 모델은 ChatGPT(GPT-3.5-Turbo)를 사용
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                openai_api_key=api_key
            )
            # 맵 프롬프트 설정: 1단계 요약에 사용
            prompt = PromptTemplate(
                template="""백틱으로 둘러싸인 전사본을 이용해 해당 유튜브 비디오를 요약해주세요.
                ```{text}``` 단, 영어로 작성해주세요.
                """, input_variables=["text"]
            )
            # 컴바인 프롬프트 설정: 2단계 요약에 사용
            combine_prompt = PromptTemplate(
                template="""백틱으로 둘러싸인 유튜브 스크립트를 모두 조합하여
                ```{text}```
                10문장 내외의 간결한 요약문을 제공해주세요. 단, 영어로 작성해주세요.
                """, input_variables=["text"]
            )
            # 랭체인을 활용하여 긴 글 요약
            # 긴 문서를 문자열 길이 3000을 기준 길이로 하여 분할
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=0)

            # 분할된 문서들은 pages라는 문자열 리스트로 저장
            # 예)
            # pages = ["텍스트1", "텍스트2", "텍스트3", "텍스트4"]
            pages = text_splitter.split_text(transcript)

            # pages를 load_summarize_chain 도구에서 처리 가능한 형식으로 변환
            # 변환 후에는 문자열이 아닌 랭체인 고유 타입으로 변환됨
            # 예)
            # text = [Document(page_content="텍스트1"), Document(page_content="텍스트2"),
            # Document(page_content="텍스트3"), Document(page_content="텍스트4")]
            # 랭체인에서 원하는 형태로 변환해야 아래 단계에서 처리 가능
            text = text_splitter.create_documents(pages)

            # map_prompt와 combine_prompt를 이용하여 두 단계 요약을 준비
            chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=False, map_prompt=prompt, combine_prompt=combine_prompt)

            # 두 단계 요약의 결과를 저장. invoke()하면 실행
            st.session_state["summarize"] = chain.invoke(text)["output_text"]
            st.success(st.session_state["summarize"])
            transe = trans(st.session_state["summarize"])
            st.subheader("Final Analysis Result (Reply in Korean)")
            st.info(transe)

if __name__ == "__main__":
    main()