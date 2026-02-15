import streamlit as st
from google import genai
import os
from googleapiclient.discovery import build # 유튜브 검색용 도구

# ==========================================
# 🔑 필수 입력: 2개의 API 키를 여기에 넣으세요!
# ==========================================
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-flash-latest"

st.set_page_config(page_title="AI Health Docent Pro", layout="wide")

# --- 🎨 오리지널 클린 UI (화이트 & 블루) ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    h1, h2, h3 { color: #2c3e50; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; background-color: #007bff; color: white; border: none; }
    .stButton>button:hover { background-color: #0056b3; color: white; }
    .report-card { background-color: white; padding: 25px; border-radius: 12px; border-left: 6px solid #007bff; box-shadow: 0 4px 10px rgba(0,0,0,0.05); color: #333; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# 확장자 자동 인식 함수
def get_image_path(base_name):
    for ext in ['.png', '.jpg', '.jpeg']:
        if os.path.exists(f"{base_name}{ext}"):
            return f"{base_name}{ext}"
    return None

# 유튜브 맞춤 영상 검색 함수
def search_youtube_video(query):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            part="snippet",
            maxResults=1,
            q=query,
            type="video",
            relevanceLanguage="ko" 
        )
        response = request.execute()
        if response['items']:
            return response['items'][0]['id']['videoId']
    except Exception as e:
        st.error(f"유튜브 검색 중 오류 발생: {e}")
    return "B2iAodr0fOo" 

if 'step' not in st.session_state: st.session_state.step = 1
if 'patient' not in st.session_state: st.session_state.patient = {}

# --- [STEP 1: 간호 사정] ---
if st.session_state.step == 1:
    st.title("🩺 단계 1: 환자 기초 데이터 사정")
    with st.form("assessment"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("성함", "재훈")
            age = st.number_input("나이", 0, 120, 24)
            gender = st.selectbox("성별", ["남성", "여성"])
        with c2:
            height = st.number_input("키 (cm)", 100.0, 250.0, 175.0)
            weight = st.number_input("몸무게 (kg)", 20.0, 200.0, 70.0)
        
        # 버튼 문구 직관적으로 수정
        if st.form_submit_button("다음 단계로 가기"):
            bmi = weight / ((height/100)**2)
            if bmi < 18.5: level = 1
            elif bmi < 23.0: level = 2
            elif bmi < 25.0: level = 3
            elif bmi < 30.0: level = 4
            else: level = 5
            
            st.session_state.patient = {
                "name": name, "age": age, "gender": gender, 
                "bmi": round(bmi, 2), "level": level
            }
            st.session_state.step = 2
            st.rerun()

# --- [STEP 2: 전신 3D 모델 및 증상 입력] ---
elif st.session_state.step == 2:
    p = st.session_state.patient
    st.title(f"👤 {p['name']}님 맞춤형 3D 아바타")
    
    col_char, col_cc = st.columns([1, 1.2])
    with col_char:
        base_name = "image_10" if p['gender'] == "남성" else "image_11"
        img_path = get_image_path(base_name)
        
        if img_path:
            st.image(img_path, use_container_width=True, caption=f"System: {p['gender']} 3D Silhouette Loaded.")
        else:
            st.warning(f"⚠️ 폴더에 '{base_name}' 파일이 없습니다.")

    with col_cc:
        st.subheader("임상 정보 입력")
        history = st.text_area("기저질환 (Past Medical History)", placeholder="예: 고혈압, 당뇨")
        cc = st.text_area("주증상 (Chief Complaint)", placeholder="예: 어제부터 시작된 숨가쁨과 흉통")
        
        # 버튼 문구 직관적으로 수정
        if st.button("다음 단계로 가기"):
            st.session_state.patient.update({"history": history, "cc": cc})
            st.session_state.step = 3
            st.rerun()

# --- [STEP 3: 3D 부위 클로즈업 및 실시간 영상/리포트] ---
elif st.session_state.step == 3:
    p = st.session_state.patient
    st.title(f"🔍 {p['name']}님 3D 정밀 분석 리포트")
    
    target_organ = "전신 (Full Body)"
    base_name = "image_10" if p['gender'] == "남성" else "image_11"
    
    if any(k in p['cc'] for k in ["기침", "숨", "호흡", "가슴", "폐", "가래"]):
        target_organ = "호흡기계 (Pulmonary System)"
        base_name = "image_4"
    elif any(k in p['cc'] for k in ["복통", "위", "소화", "속쓰림", "배", "장"]):
        target_organ = "소화기계 (Digestive System)"
        base_name = "image_5"
    elif any(k in p['cc'] for k in ["뼈", "관절", "근육", "허리", "다리", "팔", "통증"]):
        target_organ = "근골격계 (Musculoskeletal System)"
        base_name = "image_6"
    elif any(k in p['cc'] for k in ["얼굴", "눈", "코", "입", "안면"]):
        target_organ = "안면계 (Facial System)"
        base_name = "image_7"
    elif any(k in p['cc'] for k in ["머리", "두통", "어지러움", "뇌", "기억", "신경"]):
        target_organ = "신경계 (Nervous System)"
        base_name = "image_8"

    img_path = get_image_path(base_name)

    col_viz, col_vid = st.columns([1, 1.2])
    with col_viz:
        st.subheader(f"🎯 타겟 클로즈업: {target_organ}")
        if img_path:
            st.image(img_path, use_container_width=True, caption=f">> Scanning {target_organ}...")
        else:
            st.warning(f"⚠️ 폴더에 '{base_name}' 파일이 없습니다!")
        
    with col_vid:
        st.subheader(f"🎥 맞춤형 병태생리 가이드 영상")
        with st.spinner("증상에 맞는 최적의 의학 영상을 찾는 중입니다..."):
            search_keyword = f"{target_organ} {p['cc']} 병태생리 기전"
            video_id = search_youtube_video(search_keyword)
            st.video(f"https://www.youtube.com/watch?v={video_id}")

    st.markdown("---")
    st.subheader("🤖 전문 AI 도슨트 분석")
    with st.spinner("Analyzing Clinical Data..."):
        prompt = f"""
        너는 최첨단 헬스케어 시스템의 AI 도슨트이자 전문 간호사야. 
        환자(나이 {p['age']}, BMI {p['bmi']}, 기저질환 {p['history']}, 주증상 {p['cc']})에게 다음을 전문적이고 체계적으로 브리핑해줘.
        1. {p['cc']}의 병태생리 기전 ({target_organ}과 연관 지어 설명)
        2. 관련 처방 약물의 작용 기전(Mechanism of Action, MOA)
        3. 환자의 연령과 BMI를 고려한 간호 중재법
        마지막엔 "정밀 진단을 위해 빠른 시일 내에 전문의 진료를 권고합니다."로 마무리해줘.
        """
        try:
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            st.markdown(f"<div class='report-card'>{response.text}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"데이터 분석 중 시스템 오류 발생: {e}")

    # 마지막 버튼도 깔끔하게 수정
    if st.button("처음으로 돌아가기"):
        st.session_state.step = 1
        st.rerun()
