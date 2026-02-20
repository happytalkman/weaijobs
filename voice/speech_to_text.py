"""
weAID 음성 인식 (STT - Speech to Text)
사용자의 목소리를 텍스트로 변환합니다.

지원 방식:
1. 브라우저 기반: Web Speech API (JavaScript)
2. 서버 기반: Google Speech Recognition (Python)
"""
import io
import os
import base64
from typing import Optional


class SpeechToText:
    """
    서버 측 음성 인식 처리기
    오디오 데이터를 받아 텍스트로 변환합니다.
    """

    def __init__(self, language: str = "ko-KR"):
        self.language = language
        self._recognizer = None
        self._available = False
        self._init_recognizer()

    def _init_recognizer(self):
        """SpeechRecognition 라이브러리를 초기화합니다."""
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._available = True
        except ImportError:
            print("[STT] speech_recognition 라이브러리가 없습니다. 브라우저 STT를 사용하세요.")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    async def transcribe_audio_bytes(self, audio_bytes: bytes) -> str:
        """
        오디오 바이트 데이터를 텍스트로 변환합니다.

        Args:
            audio_bytes: WAV 형식의 오디오 바이트

        Returns:
            변환된 텍스트 문자열
        """
        if not self._available:
            return ""

        try:
            import speech_recognition as sr

            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._recognizer.record(source)

            text = self._recognizer.recognize_google(
                audio,
                language=self.language,
            )
            return text.strip()

        except Exception as e:
            print(f"[STT] 변환 오류: {e}")
            return ""

    async def transcribe_base64(self, audio_base64: str) -> str:
        """Base64 인코딩된 오디오를 텍스트로 변환합니다."""
        try:
            audio_bytes = base64.b64decode(audio_base64)
            return await self.transcribe_audio_bytes(audio_bytes)
        except Exception as e:
            print(f"[STT] Base64 디코딩 오류: {e}")
            return ""

    def listen_from_microphone(self, timeout: int = 5, phrase_limit: int = 30) -> str:
        """
        마이크에서 음성을 녹음하여 텍스트로 변환합니다.
        CLI 사용 시 활용합니다.

        Args:
            timeout: 음성 감지 대기 시간 (초)
            phrase_limit: 최대 발화 시간 (초)

        Returns:
            변환된 텍스트
        """
        if not self._available:
            print("[STT] 음성 인식을 사용할 수 없습니다.")
            return ""

        try:
            import speech_recognition as sr

            with sr.Microphone() as source:
                print("🎤 말씀해 주세요...")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit,
                )

            print("🔄 음성 인식 중...")
            text = self._recognizer.recognize_google(
                audio,
                language=self.language,
            )
            print(f"📝 인식됨: {text}")
            return text.strip()

        except Exception as e:
            print(f"[STT] 마이크 오류: {e}")
            return ""


# 브라우저 Web Speech API JavaScript 코드
WEB_SPEECH_API_JS = """
// weAID Web Speech API - 브라우저 음성 인식
class WeAIDVoice {
    constructor(onResult, onStart, onEnd, onError) {
        this.onResult = onResult;
        this.onStart = onStart || (() => {});
        this.onEnd = onEnd || (() => {});
        this.onError = onError || (() => {});
        this.recognition = null;
        this.isListening = false;
        this.language = 'ko-KR';
        this._init();
    }

    _init() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error('[weAID] 이 브라우저는 음성 인식을 지원하지 않습니다.');
            this.onError('음성 인식이 지원되지 않는 브라우저입니다.');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = this.language;
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
            this.isListening = true;
            this.onStart();
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.onEnd();
        };

        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            if (finalTranscript) {
                this.onResult(finalTranscript, true);
            } else if (interimTranscript) {
                this.onResult(interimTranscript, false);
            }
        };

        this.recognition.onerror = (event) => {
            this.isListening = false;
            this.onError(event.error);
        };
    }

    start() {
        if (this.recognition && !this.isListening) {
            this.recognition.start();
        }
    }

    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    toggle() {
        if (this.isListening) {
            this.stop();
        } else {
            this.start();
        }
    }
}
"""

# 싱글턴
stt = SpeechToText()
