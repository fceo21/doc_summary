# 문서요약 플러그인

**Groq Llama 3.1/2로 PDF/TXT/음성 파일을 처리. 실시간 사용량 표시. Claude 비용 0.**

## 핵심 기능

✅ **전문 또는 요약** — 100%, 50%, 20% 선택  
✅ **모델 선택** — Llama 3.1 (정확도) vs Llama 2 (50% 토큰절약)  
✅ **📊 사용량 표시** — 파일 입력 시 현재 잔여량, 결과에 사용량 자동 표시  
✅ **OCR 자동** — 스캔 PDF도 텍스트 추출  
✅ **대용량 처리** — 최대 10MB (자동 청킹)  
✅ **Markdown 출력** — 복사해서 바로 사용  
✅ **무료** — Groq 프리 티어만 사용  

---

## 빠른 시작

### 1단계: Groq API 키 발급
https://console.groq.com → 무료 가입 → API 키 복사

### 2단계: 환경변수 설정
`C:\cowork\.claude\.env` 파일 생성:
```
GROQ_API_KEY=gsk_your_key_here
```

### 3단계: 플러그인 설치
Cowork에서 "플러그인 설치" → 이 디렉토리 선택

### 4단계: 사용
```
/문서요약

파일 경로: C:\Documents\example.pdf
출력 모드: [50% 요약 선택]
모델: [Llama 2 선택 (토큰절약)]

→ Markdown 결과 + 📊 사용량 표시
```

---

## 필수 라이브러리

```bash
pip install groq PyPDF2 pdf2image pytesseract pillow requests
```

**Tesseract OCR** (Windows):  
https://github.com/UB-Mannheim/tesseract/wiki 에서 설치 프로그램 다운로드

---

## 모델 비교

| 항목 | Llama 3.1 | Llama 2 |
|------|-----------|---------|
| **정확도** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **토큰 사용** | 100% | **50%** |
| **속도** | 보통 | 빠름 |
| **추천** | 정확성 우선 | 토큰 절약 |

---

## 파일 구조

```
document-summarizer/
├── skills/document-summarizer/
│   ├── SKILL.md              # 사용자 안내
│   └── references/
│       ├── setup.md          # 초기 설정
│       └── usage.md          # 사용 예시
├── scripts/
│   └── groq_processor.py     # 핵심 처리 스크립트
└── README.md                 # 이 파일
```

---

## 비용

| 항목 | 비용 | 설명 |
|------|------|------|
| Groq Llama | 무료 | 프리 티어 (초당 30토큰) |
| Claude | $0 | 사용하지 않음 |
| **월 요금** | **$0** | 개인 사용 범위 |

Llama 2로 전환하면 토큰 사용량 50% 절약 가능

---

## 제한사항

- **최대 파일**: 10MB
- **지원 형식**: PDF, TXT, 마크다운
- **언어**: 한글 + 영문 최적화
- **처리 시간**: 파일 크기에 따라 30초~3분
- **프리 티어**: 초당 30토큰 제한 (월 리셋)

---

## 사용량 모니터링

**파일 입력 시 자동 표시:**
```
📊 Groq 사용량
- 총 사용 토큰: 2,450
- 프롬프트: 1,200
- 완료: 1,250
- 모델: Llama 2 (토큰절약 50%)
- 토큰 효율: 50%
```

---

## 문제 해결

**"GROQ_API_KEY 없음" 에러**
→ `C:\cowork\.claude\.env` 파일 생성 & API 키 저장

**"파이썬 모듈 없음" 에러**
→ `pip install groq PyPDF2 pdf2image pytesseract pillow requests`

**"사용량 표시 안 됨"**
→ Groq API가 사용량 조회 미지원할 수 있음 (기능은 정상작동)

**OCR 결과 형편없음**
→ 스캔 PDF 해상도 200dpi 이상으로 다시 스캔

---

## 기술 스택

- **Groq SDK** (Python)
- **Llama 3.1 / 2** (언어 모델)
- **PyPDF2** (텍스트 추출)
- **pytesseract** (OCR)
- **Cowork** (플러그인 프레임워크)

---

## 라이선스

MIT (자유롭게 수정/배포 가능)
