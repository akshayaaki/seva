'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Globe2, AlertCircle } from 'lucide-react';

interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
}

const SUPPORTED_LANGUAGES = [
  { code: 'en-IN', label: 'English (India)' },
  { code: 'hi-IN', label: 'Hindi' },
  { code: 'mr-IN', label: 'Marathi' },
  { code: 'gu-IN', label: 'Gujarati' },
  { code: 'bn-IN', label: 'Bengali' },
  { code: 'ta-IN', label: 'Tamil' },
  { code: 'te-IN', label: 'Telugu' },
  { code: 'kn-IN', label: 'Kannada' },
];

export default function VoiceRecorder({ onTranscription }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [selectedLang, setSelectedLang] = useState('en-IN');
  const [error, setError] = useState<string | null>(null);
  const [interimText, setInterimText] = useState('');
  const onTranscriptionRef = useRef(onTranscription);
  onTranscriptionRef.current = onTranscription;
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError('Voice input is not supported in this browser. Please type or use Chrome/Edge.');
      return;
    }

    let isCleaningUp = false;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = selectedLang;

    recognition.onresult = (event: any) => {
      let currentInterim = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        } else {
          currentInterim += event.results[i][0].transcript;
        }
      }

      setInterimText(currentInterim);
      if (finalTranscript && onTranscriptionRef.current) {
        onTranscriptionRef.current(finalTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      if (isCleaningUp || event.error === 'aborted') {
        // Normal intentional stop or cleanup
        setIsRecording(false);
        return;
      }

      if (event.error === 'no-speech') {
        setIsRecording(false);
        return;
      }

      if (event.error === 'not-allowed') {
        setError('Microphone permission denied. Please allow microphone access.');
      } else {
        console.warn('Speech recognition notice:', event.error);
        setError(`Voice recognition issue: ${event.error}`);
      }
      setIsRecording(false);
    };

    recognition.onend = () => {
      if (!isCleaningUp) {
        setIsRecording(false);
        setInterimText('');
      }
    };

    recognitionRef.current = recognition;

    return () => {
      isCleaningUp = true;
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore
        }
      }
    };
  }, [selectedLang]);

  const toggleRecording = () => {
    setError(null);
    if (!recognitionRef.current) {
      setError('Voice recognition engine unavailable.');
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        recognitionRef.current.lang = selectedLang;
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err: any) {
        console.error('Failed to start recording:', err);
        setError('Could not start microphone.');
      }
    }
  };

  return (
    <div className="bg-[#F4F7FA] rounded-2xl p-4 border border-[#CBD5E1] shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <Globe2 className="w-4 h-4 text-[#1E6FFF]" />
          <label htmlFor="voice-lang-select" className="text-xs font-bold text-[#102A43]">
            Spoken Language:
          </label>
          <select
            id="voice-lang-select"
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            disabled={isRecording}
            className="text-xs bg-[#FFFFFF] border border-[#CBD5E1] rounded-lg px-2.5 py-1 text-[#102A43] focus:outline-none focus:border-[#1E6FFF] font-medium"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          onClick={toggleRecording}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-xs tracking-wide transition-all shadow-sm cursor-pointer ${
            isRecording
              ? 'bg-[#EF4444] hover:bg-[#DC2626] text-[#FFFFFF] animate-pulse'
              : 'bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF]'
          }`}
        >
          {isRecording ? (
            <>
              <MicOff className="w-4 h-4" />
              <span>Stop Speaking</span>
            </>
          ) : (
            <>
              <Mic className="w-4 h-4 text-[#FFFFFF]" />
              <span>Record Voice</span>
            </>
          )}
        </button>
      </div>

      {isRecording && (
        <div className="mt-2 p-3 bg-[#E8F5E9] border border-[#10B981]/30 rounded-xl flex items-center gap-3">
          <div className="flex gap-1 items-center">
            <span className="w-1.5 h-4 bg-[#10B981] rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-6 bg-[#10B981] rounded-full animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1.5 h-5 bg-[#10B981] rounded-full animate-bounce" />
          </div>
          <p className="text-xs text-[#102A43] italic font-medium">
            Listening... {interimText ? `"${interimText}"` : 'Please speak your grievance clearly.'}
          </p>
        </div>
      )}

      {error && (
        <div className="mt-2 p-2.5 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl flex items-center gap-2 text-[#EF4444] text-xs font-medium">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

