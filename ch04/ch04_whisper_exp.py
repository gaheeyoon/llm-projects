from openai import OpenAI

# API 키 입력
client = OpenAI(api_key="여기에 API 키를 넣어주세요")

# 녹음 파일 열기
audio_file = open("speech.mp3", "rb")

# Whisper 모델에 음원 파일 넣기
transcript = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file, 
    response_format="text"
)

# 결과 보기
print(transcript)