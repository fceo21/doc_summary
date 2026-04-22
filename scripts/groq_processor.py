#!/usr/bin/env python3
"""
Groq Llama 문서 처리기
- PDF/TXT/음성 파일 입력
- OCR (스캔 PDF)
- Groq API로 전문/요약 생성 (Llama 3.1 또는 2 선택)
- Markdown 출력
- 사용량 조회
"""

import os
import sys
import json
import requests
from pathlib import Path
from groq import Groq

def load_api_key():
    """환경변수에서 Groq API 키 로드"""
    # 1. 직접 환경변수
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        return api_key

    # 2. .env 파일에서 로드
    env_paths = [
        Path("C:\\cowork\\.claude\\.env"),
        Path.home() / ".cowork" / ".claude" / ".env",
        Path(".env")
    ]

    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        return line.split("=", 1)[1].strip()

    raise ValueError("GROQ_API_KEY를 찾을 수 없습니다. C:\\cowork\\.claude\\.env에 저장하세요.")

def get_groq_usage(api_key):
    """Groq API 사용량 조회"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.groq.com/openai/v1/usage",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "total_tokens": data.get("data", {}).get("total_tokens", 0),
                "completion_tokens": data.get("data", {}).get("completion_tokens", 0),
                "prompt_tokens": data.get("data", {}).get("prompt_tokens", 0)
            }
    except:
        pass

    # 사용량 조회 실패 시 기본값 반환
    return None

MODEL_INFO = {
    "3": {
        "name": "llama-3.1-70b-versatile",
        "display": "Llama 3.1 (최고 품질)",
        "token_ratio": 1.0,
        "note": "가장 정확한 요약"
    },
    "2": {
        "name": "llama-2-70b-chat",
        "display": "Llama 2 (토큰절약 50%)",
        "token_ratio": 0.5,
        "note": "빠르고 경제적"
    }
}

def read_file(file_path):
    """파일 읽기 (PDF OCR, TXT, 음성 전사본)"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"파일 없음: {file_path}")

    if path.suffix.lower() == ".pdf":
        return read_pdf(path)
    elif path.suffix.lower() in [".txt", ".md"]:
        with open(path, encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"지원하지 않는 형식: {path.suffix}")

def read_pdf(pdf_path):
    """PDF 읽기 (OCR 포함)"""
    try:
        import PyPDF2
    except ImportError:
        raise ImportError("PyPDF2를 설치하세요: pip install PyPDF2")

    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
    except Exception as e:
        # PDF 읽기 실패 시 스캔 문서로 간주하고 pytesseract 시도
        try:
            return read_pdf_ocr(pdf_path)
        except:
            raise ValueError(f"PDF 읽기 실패: {e}")

    return text if text.strip() else read_pdf_ocr(pdf_path)

def read_pdf_ocr(pdf_path):
    """Pytesseract를 사용한 OCR"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        raise ImportError(
            "OCR 라이브러리 필요:\n"
            "pip install pdf2image pytesseract pillow\n"
            "Tesseract 설치: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    images = convert_from_path(pdf_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang="kor+eng")
        text += "\n---\n"

    return text

def chunk_text(text, max_tokens=5000):
    """큰 텍스트를 청크로 분할 (대략 4000자 = 1000토큰)"""
    chunk_size = max_tokens * 4
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])

    return chunks if chunks else [text]

def process_with_groq(text, mode="50", model="3", api_key=""):
    """Groq Llama로 처리 (모델 선택 가능)"""
    client = Groq(api_key=api_key)

    model_name = MODEL_INFO[model]["name"]

    # 모드별 프롬프트
    if mode == "100":
        prompt = f"""다음 문서를 마크다운 형식으로 정리하세요.
- 섹션별 제목 (# ## ###)
- 핵심 내용은 굵은글씨나 강조
- 리스트는 - 또는 번호 매김
- 원본 의미 손상 없이 구조화만

---

{text}"""
    elif mode == "50":
        prompt = f"""다음 문서의 핵심 50%만 마크다운으로 요약하세요.
- 주요 내용, 결정사항, 데이터만 포함
- 불필요한 설명은 제외
- 마크다운 형식 (#, -, *)

---

{text}"""
    else:  # 20%
        prompt = f"""다음 문서를 5줄 이내로 핵심만 마크다운 정리하세요.
- 가장 중요한 것 3가지
- 간결하게

---

{text}"""

    response = client.messages.create(
        model=model_name,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000
    )

    return response.content[0].text

def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "사용법: python groq_processor.py <파일경로> <모드> [모델]",
            "modes": {"100": "전문", "50": "50% 요약", "20": "20% 요약"},
            "models": {"3": "Llama 3.1", "2": "Llama 2 (50% 토큰절약)"}
        }))
        sys.exit(1)

    file_path = sys.argv[1]
    mode = sys.argv[2]  # "100", "50", "20"
    model = sys.argv[3] if len(sys.argv) > 3 else "3"  # "3" 또는 "2"

    try:
        # API 키 로드
        api_key = load_api_key()

        # 사용량 조회
        print(f"📊 Groq 사용량 확인 중...", file=sys.stderr)
        usage = get_groq_usage(api_key)

        # 파일 읽기
        print(f"📄 파일 읽기 중: {file_path}", file=sys.stderr)
        text = read_file(file_path)

        # 청킹
        chunks = chunk_text(text)
        print(f"📊 {len(chunks)}개 청크로 분할 처리 중...", file=sys.stderr)
        print(f"🤖 모델: {MODEL_INFO[model]['display']}", file=sys.stderr)

        # Groq 처리
        results = []
        for i, chunk in enumerate(chunks, 1):
            print(f"⚙️ 청크 {i}/{len(chunks)} 처리 중...", file=sys.stderr)
            result = process_with_groq(chunk, mode, model, api_key)
            results.append(result)

        # 결과 합치기
        final_result = "\n\n---\n\n".join(results)

        # 사용량 표시 (마크다운)
        usage_note = ""
        if usage:
            usage_note = f"""

---

## 📊 Groq 사용량
- **총 사용 토큰**: {usage.get('total_tokens', '정보 없음'):,}
- **프롬프트**: {usage.get('prompt_tokens', 0):,}
- **완료**: {usage.get('completion_tokens', 0):,}
- **모델**: {MODEL_INFO[model]['display']}
- **토큰 효율**: {MODEL_INFO[model]['token_ratio']*100:.0f}%
"""

        final_result = final_result + usage_note

        # JSON 출력 (Cowork에서 파싱)
        print(json.dumps({
            "status": "success",
            "mode": mode,
            "model": model,
            "file": file_path,
            "result": final_result,
            "chunks": len(chunks),
            "usage": usage
        }, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "file": file_path
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
