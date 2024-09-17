##### 기본 정보 입력 ####
# 스트림릿 패키지 추가
import streamlit as st

# OpenAI 패키지 추가
from openai import OpenAI

# 이미지를 처리하기 위한 파이썬 기본 패키지
import os
import io
import base64
from PIL import Image

# GPT-4V와 TTS를 위해서 client 객체를 선언
api_key = "여기에 API 키를 넣어주세요"
client = OpenAI(
    api_key=api_key
)

##### 기능 구현 함수 정리#####
# GPT-4V
def describe(image):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 이미지에 대해서 아주 자세히 묘사해줘"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image,
                        },
                    },
                ],
            }
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content

# TTS
def TTS(response):
    # TTS를 활용하여 만든 음성을 파일로 저장
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="onyx",
        input=response
    ) as response:
        filename="output.mp3"
        response.stream_to_file(filename)

    # 저장한 음성 파일을 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        # HTML 문법을 사용하여 자동으로 음원을 재생하는 코드를 작성
        # 스트림릿에서 HTML을 사용할 수 있는 st.markdown()을 활용
        md = f'''
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            '''
        st.markdown(md, unsafe_allow_html=True)

    # 폴더에 남지 않도록 파일을 삭제
    os.remove(filename)

##### 메인 함수#####
def main():
    st.image('ai.png', width=200)
    st.title("이미지를 해설해드립니다.")

    # 이미지를 업로드
    img_file_buffer = st.file_uploader('Upload a PNG image', type='png')

    if img_file_buffer is not None:
        image = Image.open(img_file_buffer)

    # 업로드한 이미지를 화면에 출력
    st.image(image, caption='Uploaded Image.', use_column_width=True)
    
    # 이미지 => 바이트 버퍼로 변환
    buffered = io.BytesIO()
    image.save(buffered, format='PNG')
    
    # 바이트 버퍼 => Base64 인코딩 바이트 문자열로 변환
    img_base64 = base64.b64encode(buffered.getvalue())
    
    # Base64 인코딩 바이트 문자열 => UTF-8 문자열로 디코딩
    img_base64_str = img_base64.decode('utf-8')
    
    # GPT-4V에서 입력받을 수 있는 형태로 변환
    # 예시 참고: https://platform.openai.com/docs/guides/vision/uploading-base-64-encoded-images
    image = f"data:image/jpeg;base64,{img_base64_str}"
    
    # GPT4V가 이미지에 대한 설명을 반환하고 이를 st.info()로 출력
    text = describe(image)
    st.info(text)
    
    # 이미지에 대한 설명을 음성으로 변환
    TTS(text)

if __name__=="__main__":
    main()