#!/usr/bin/env python3
"""
문서요약 웹 인터페이스
http://localhost:5000 에서 실행
"""

from flask import Flask, render_template_string, request, jsonify
import json
import subprocess
import sys
from pathlib import Path

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📄 문서요약 - Groq Llama</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }
        input[type="text"], select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 28px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102,126,234,0.4);
        }
        button:active {
            transform: translateY(0);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        .spinner {
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result {
            display: none;
            margin-top: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }
        .result pre {
            background: white;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.6;
            color: #333;
        }
        .error {
            color: #e74c3c;
            padding: 15px;
            background: #fee;
            border-radius: 6px;
            margin-top: 20px;
            border-left: 4px solid #e74c3c;
        }
        .success {
            color: #27ae60;
            padding: 15px;
            background: #efe;
            border-radius: 6px;
            margin-top: 20px;
            border-left: 4px solid #27ae60;
        }
        .usage {
            font-size: 12px;
            color: #666;
            margin-top: 10px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 문서요약</h1>
        <p class="subtitle">Groq Llama 3.1 / 2로 PDF, TXT, 음성 파일 처리</p>

        <form id="form">
            <div class="form-group">
                <label>📁 파일 경로</label>
                <input type="text" id="filepath" placeholder="C:\Documents\example.pdf" required>
            </div>

            <div class="grid">
                <div class="form-group">
                    <label>📊 출력 모드</label>
                    <select id="mode" required>
                        <option value="100">전문 (100%)</option>
                        <option value="50" selected>요약 (50%)</option>
                        <option value="20">요약 (20%)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>🤖 모델</label>
                    <select id="model" required>
                        <option value="3">Llama 3.1 (정확)</option>
                        <option value="2">Llama 2 (50% 절약)</option>
                    </select>
                </div>
            </div>

            <button type="submit">⚡ 처리 시작</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 15px;">처리 중...</p>
        </div>

        <div class="result" id="result">
            <h3>✅ 결과</h3>
            <pre id="resultText"></pre>
            <div class="usage" id="usage"></div>
        </div>

        <div id="message"></div>
    </div>

    <script>
        document.getElementById('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const filepath = document.getElementById('filepath').value;
            const mode = document.getElementById('mode').value;
            const model = document.getElementById('model').value;
            const message = document.getElementById('message');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');

            // 유효성 검사
            if (!filepath) {
                message.innerHTML = '<div class="error">❌ 파일 경로를 입력하세요</div>';
                return;
            }

            loading.style.display = 'block';
            result.style.display = 'none';
            message.innerHTML = '';

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filepath, mode, model })
                });

                const data = await response.json();
                loading.style.display = 'none';

                if (data.error) {
                    message.innerHTML = `<div class="error">❌ ${data.error}</div>`;
                } else {
                    document.getElementById('resultText').textContent = data.result;
                    if (data.usage) {
                        document.getElementById('usage').innerHTML = 
                            `📊 사용량: ${data.usage.total_tokens}토큰 | ` +
                            `모델: ${data.model_name} | ` +
                            `효율: ${data.token_ratio}%`;
                    }
                    result.style.display = 'block';
                    message.innerHTML = '<div class="success">✅ 완료!</div>';
                }
            } catch (err) {
                loading.style.display = 'none';
                message.innerHTML = `<div class="error">❌ ${err.message}</div>`;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.json
        filepath = data.get('filepath')
        mode = data.get('mode', '50')
        model = data.get('model', '3')

        # groq_processor.py 실행
        result = subprocess.run(
            [sys.executable, 'groq_processor.py', filepath, mode, model],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )

        if result.returncode != 0:
            return jsonify({'error': result.stderr or '처리 실패'}), 400

        output = json.loads(result.stdout)
        
        if 'error' in output:
            return jsonify({'error': output['error']}), 400

        model_names = {'3': 'Llama 3.1', '2': 'Llama 2'}
        token_ratios = {'3': '100', '2': '50'}

        return jsonify({
            'status': 'success',
            'result': output['result'],
            'usage': output.get('usage'),
            'model_name': model_names.get(model, 'Unknown'),
            'token_ratio': token_ratios.get(model, '100')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 웹 서버 시작: http://localhost:5000")
    print("브라우저에서 위 주소로 접속하세요")
    app.run(debug=False, port=5000, host='127.0.0.1')
