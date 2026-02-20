"""
weAID 음성 합성 (TTS - Text to Speech)
AI 응답을 음성으로 변환합니다.

지원 방식:
1. 브라우저 기반: Web Speech Synthesis API (JavaScript)
2. 서버 기반: gTTS (Google Text-to-Speech)
"""
import io
import os
import base64
import tempfile
import asyncio
from typing import Optional


class TextToSpeech:
    """
    서버 측 음성 합성 처리기
    텍스트를 오디오 데이터로 변환합니다.
    """

    def __init__(self, language: str = "ko", engine: str = "gtts"):
        self.language = language
        self.engine = engine
        self._gtts_available = False
        self._pyttsx3_available = False
        self._check_engines()

    def _check_engines(self):
        """사용 가능한 TTS 엔진을 확인합니다."""
        try:
            from gtts import gTTS
            self._gtts_available = True
        except ImportError:
            pass

        try:
            import pyttsx3
            self._pyttsx3_available = True
        except ImportError:
            pass

    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        텍스트를 MP3 오디오 바이트로 변환합니다.

        Args:
            text: 변환할 텍스트

        Returns:
            MP3 형식의 오디오 바이트 (실패시 None)
        """
        # 텍스트 정리 (마크다운 제거)
        clean_text = self._clean_text(text)

        if self.engine == "gtts" and self._gtts_available:
            return await self._synthesize_gtts(clean_text)
        elif self._pyttsx3_available:
            return await self._synthesize_pyttsx3(clean_text)
        return None

    async def synthesize_base64(self, text: str) -> Optional[str]:
        """텍스트를 Base64 인코딩된 MP3로 변환합니다."""
        audio_bytes = await self.synthesize(text)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode("utf-8")
        return None

    async def _synthesize_gtts(self, text: str) -> Optional[bytes]:
        """Google TTS로 음성을 생성합니다."""
        try:
            from gtts import gTTS

            def _generate():
                tts = gTTS(text=text, lang=self.language, slow=False)
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                return buf.read()

            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(None, _generate)
            return audio_bytes
        except Exception as e:
            print(f"[TTS] gTTS 오류: {e}")
            return None

    async def _synthesize_pyttsx3(self, text: str) -> Optional[bytes]:
        """pyttsx3로 음성을 생성합니다."""
        try:
            import pyttsx3

            def _generate():
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.setProperty("volume", 0.9)

                # 한국어 설정 시도
                voices = engine.getProperty("voices")
                for voice in voices:
                    if "ko" in voice.languages or "Korean" in voice.name:
                        engine.setProperty("voice", voice.id)
                        break

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    tmp_path = f.name

                engine.save_to_file(text, tmp_path)
                engine.runAndWait()

                with open(tmp_path, "rb") as f:
                    data = f.read()
                os.unlink(tmp_path)
                return data

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            print(f"[TTS] pyttsx3 오류: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """마크다운 문법을 제거하고 음성에 적합한 텍스트로 변환합니다."""
        import re
        # 마크다운 헤더 제거
        text = re.sub(r"#{1,6}\s+", "", text)
        # 굵은 글씨, 기울임 제거
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        # 코드 블록 제거
        text = re.sub(r"```[^`]*```", "코드 예시가 있습니다.", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # 링크 제거
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # 불릿 포인트 정리
        text = re.sub(r"^[\-\*\+]\s+", "- ", text, flags=re.MULTILINE)
        # 번호 목록 정리
        text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
        # 연속 빈 줄 정리
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 너무 긴 텍스트는 잘라냄 (TTS 품질 유지)
        if len(text) > 1000:
            text = text[:1000] + "... 자세한 내용은 화면을 확인해 주세요."
        return text.strip()

    @property
    def is_available(self) -> bool:
        return self._gtts_available or self._pyttsx3_available


# 브라우저 Web Speech Synthesis API JavaScript
WEB_SPEECH_SYNTHESIS_JS = """
// weAID Web Speech Synthesis - 브라우저 음성 합성
class WeAIDSpeech {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voice = null;
        this.rate = 1.0;
        this.pitch = 1.0;
        this.volume = 1.0;
        this.language = 'ko-KR';
        this.isSpeaking = false;
        this._loadVoice();
    }

    _loadVoice() {
        const loadVoices = () => {
            const voices = this.synth.getVoices();
            // 한국어 음성 우선 선택
            this.voice = voices.find(v => v.lang === 'ko-KR') ||
                         voices.find(v => v.lang.startsWith('ko')) ||
                         voices[0];
        };

        loadVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    speak(text) {
        if (!text || !this.synth) return;

        // 이전 발화 중단
        this.stop();

        // 마크다운 정리
        const cleanText = text
            .replace(/#{1,6}\\s+/g, '')
            .replace(/\\*{1,3}([^*]+)\\*{1,3}/g, '$1')
            .replace(/```[^`]*```/gs, '코드 예시가 있습니다.')
            .replace(/`([^`]+)`/g, '$1')
            .replace(/\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1')
            .replace(/^[\\-\\*\\+]\\s+/gm, '')
            .replace(/^\\d+\\.\\s+/gm, '');

        // 1000자 제한
        const limitedText = cleanText.length > 1000
            ? cleanText.substring(0, 1000) + '... 자세한 내용은 화면을 확인해 주세요.'
            : cleanText;

        const utterance = new SpeechSynthesisUtterance(limitedText);
        utterance.lang = this.language;
        utterance.rate = this.rate;
        utterance.pitch = this.pitch;
        utterance.volume = this.volume;

        if (this.voice) {
            utterance.voice = this.voice;
        }

        utterance.onstart = () => { this.isSpeaking = true; };
        utterance.onend = () => { this.isSpeaking = false; };
        utterance.onerror = (e) => {
            this.isSpeaking = false;
            console.error('[weAID TTS]', e);
        };

        this.synth.speak(utterance);
    }

    stop() {
        if (this.synth) {
            this.synth.cancel();
            this.isSpeaking = false;
        }
    }

    pause() {
        if (this.synth && this.isSpeaking) {
            this.synth.pause();
        }
    }

    resume() {
        if (this.synth) {
            this.synth.resume();
        }
    }

    setRate(rate) { this.rate = Math.max(0.5, Math.min(2.0, rate)); }
    setPitch(pitch) { this.pitch = Math.max(0.5, Math.min(2.0, pitch)); }
    setVolume(volume) { this.volume = Math.max(0, Math.min(1, volume)); }
}
"""

# 싱글턴
tts = TextToSpeech()
