# Audio & Speech

## expo-audio (Recording & Playback)

Works in Expo Go. Replaces the older expo-av for audio.

### Installation

```bash
npx expo install expo-audio
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "expo-audio",
        {
          "microphonePermission": "Allow $(PRODUCT_NAME) to access microphone"
        }
      ]
    ]
  }
}
```

### Audio Playback

```typescript
import { useAudioPlayer } from 'expo-audio';

function MusicPlayer() {
  const player = useAudioPlayer(require('./audio/music.mp3'));
  
  // Or from URL
  // const player = useAudioPlayer({ uri: 'https://example.com/audio.mp3' });

  return (
    <View>
      <Button title="Play" onPress={() => player.play()} />
      <Button title="Pause" onPress={() => player.pause()} />
      <Button title="Stop" onPress={() => player.stop()} />
    </View>
  );
}
```

### Advanced Playback

```typescript
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { useState } from 'react';

function AdvancedPlayer({ source }: { source: string }) {
  const player = useAudioPlayer({ uri: source });
  const status = useAudioPlayerStatus(player);

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const seek = (positionMs: number) => {
    player.seekTo(positionMs);
  };

  return (
    <View>
      <Text>{status.isPlaying ? 'Playing' : 'Paused'}</Text>
      <Text>
        {formatTime(status.currentTime)} / {formatTime(status.duration)}
      </Text>
      
      <Slider
        value={status.currentTime}
        maximumValue={status.duration}
        onSlidingComplete={seek}
      />
      
      <Button
        title={status.isPlaying ? 'Pause' : 'Play'}
        onPress={() => status.isPlaying ? player.pause() : player.play()}
      />
      
      {/* Volume control */}
      <Slider
        value={player.volume}
        maximumValue={1}
        onValueChange={(v) => player.setVolume(v)}
      />
    </View>
  );
}
```

### Audio Recording

```typescript
import { useAudioRecorder, AudioModule, RecordingOptions } from 'expo-audio';
import { useState } from 'react';

function VoiceRecorder() {
  const recorder = useAudioRecorder(RecordingOptions.HIGH_QUALITY);
  const [recordingUri, setRecordingUri] = useState<string | null>(null);

  const startRecording = async () => {
    // Request permission
    const { granted } = await AudioModule.requestRecordingPermissionsAsync();
    if (!granted) return;

    // Start recording
    recorder.record();
  };

  const stopRecording = async () => {
    await recorder.stop();
    setRecordingUri(recorder.uri);
  };

  return (
    <View>
      <Text>Status: {recorder.isRecording ? 'Recording...' : 'Ready'}</Text>
      
      {!recorder.isRecording ? (
        <Button title="Start Recording" onPress={startRecording} />
      ) : (
        <Button title="Stop Recording" onPress={stopRecording} />
      )}
      
      {recordingUri && (
        <Text>Saved to: {recordingUri}</Text>
      )}
    </View>
  );
}
```

### Recording Options

```typescript
import { RecordingOptions } from 'expo-audio';

// Preset quality options
RecordingOptions.HIGH_QUALITY   // Best quality, larger files
RecordingOptions.LOW_QUALITY    // Smaller files, lower quality

// Custom options
const customOptions = {
  extension: '.m4a',
  sampleRate: 44100,
  numberOfChannels: 2,
  bitRate: 128000,
  android: {
    outputFormat: 'mpeg4',
    audioEncoder: 'aac',
  },
  ios: {
    outputFormat: 'aac',
    audioQuality: 'max',
    linearPCMBitDepth: 16,
    linearPCMIsBigEndian: false,
    linearPCMIsFloat: false,
  },
};
```

---

## expo-speech (Text-to-Speech)

Works in Expo Go. Uses system TTS engine.

### Installation

```bash
npx expo install expo-speech
```

### Basic TTS

```typescript
import * as Speech from 'expo-speech';

const speak = (text: string) => {
  Speech.speak(text, {
    language: 'en-US',
    pitch: 1.0,    // 0.5 - 2.0
    rate: 1.0,     // 0.1 - 2.0
    onStart: () => console.log('Started speaking'),
    onDone: () => console.log('Finished speaking'),
    onError: (error) => console.error(error),
  });
};

const stopSpeaking = () => {
  Speech.stop();
};

const pauseSpeaking = async () => {
  await Speech.pause();
};

const resumeSpeaking = async () => {
  await Speech.resume();
};

// Check if speaking
const checkSpeaking = async () => {
  const speaking = await Speech.isSpeakingAsync();
  return speaking;
};
```

### Available Voices

```typescript
import * as Speech from 'expo-speech';

const getVoices = async () => {
  const voices = await Speech.getAvailableVoicesAsync();
  
  // Filter by language
  const englishVoices = voices.filter(v => v.language.startsWith('en'));
  
  // Use specific voice
  Speech.speak('Hello', {
    voice: englishVoices[0].identifier,
  });
  
  return voices;
};

// Voice object structure:
// {
//   identifier: 'com.apple.ttsbundle.Samantha-compact',
//   name: 'Samantha',
//   quality: 'Default',
//   language: 'en-US'
// }
```

---

## @jamsch/expo-speech-recognition (Speech-to-Text)

On-device speech recognition. Requires development build.

### Installation

```bash
npm install @jamsch/expo-speech-recognition
npx expo prebuild --clean
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "@jamsch/expo-speech-recognition",
        {
          "microphonePermission": "Allow $(PRODUCT_NAME) to use microphone for voice input",
          "speechRecognitionPermission": "Allow $(PRODUCT_NAME) to use speech recognition"
        }
      ]
    ]
  }
}
```

### Basic Speech Recognition

```typescript
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from '@jamsch/expo-speech-recognition';
import { useState } from 'react';

function SpeechToText() {
  const [transcript, setTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);

  // Listen for results
  useSpeechRecognitionEvent('result', (event) => {
    const text = event.results[0]?.transcript || '';
    setTranscript(text);
  });

  useSpeechRecognitionEvent('start', () => setIsListening(true));
  useSpeechRecognitionEvent('end', () => setIsListening(false));
  useSpeechRecognitionEvent('error', (event) => {
    console.error('Speech error:', event.error);
    setIsListening(false);
  });

  const startListening = async () => {
    const { granted } = await ExpoSpeechRecognitionModule.requestPermissionsAsync();
    if (!granted) return;

    ExpoSpeechRecognitionModule.start({
      lang: 'en-US',
      interimResults: true,      // Get results as user speaks
      continuous: false,          // Stop after silence
      maxAlternatives: 1,
    });
  };

  const stopListening = () => {
    ExpoSpeechRecognitionModule.stop();
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 18, minHeight: 100 }}>{transcript}</Text>
      
      <Button
        title={isListening ? 'Stop' : 'Start Listening'}
        onPress={isListening ? stopListening : startListening}
      />
    </View>
  );
}
```

### Continuous Recognition

```typescript
const startContinuousListening = () => {
  ExpoSpeechRecognitionModule.start({
    lang: 'en-US',
    interimResults: true,
    continuous: true,  // Keep listening until stopped
  });
};
```

### Available Languages

```typescript
const languages = await ExpoSpeechRecognitionModule.getSupportedLocales();
// Returns array like ['en-US', 'en-GB', 'es-ES', 'fr-FR', ...]
```

### On-Device vs Cloud

```typescript
// Check if on-device recognition is available
const isOnDevice = await ExpoSpeechRecognitionModule.isRecognitionAvailable();

// Force on-device (iOS 13+, some Android)
ExpoSpeechRecognitionModule.start({
  lang: 'en-US',
  requiresOnDeviceRecognition: true, // Fails if not available
});
```

---

## Alternative: @react-native-voice/voice

Older library, still maintained. Similar functionality.

```bash
npm install @react-native-voice/voice
```

```typescript
import Voice from '@react-native-voice/voice';
import { useEffect, useState } from 'react';

function VoiceRecognition() {
  const [results, setResults] = useState<string[]>([]);

  useEffect(() => {
    Voice.onSpeechResults = (e) => {
      setResults(e.value || []);
    };

    Voice.onSpeechError = (e) => {
      console.error(e);
    };

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const start = async () => {
    try {
      await Voice.start('en-US');
    } catch (e) {
      console.error(e);
    }
  };

  const stop = async () => {
    try {
      await Voice.stop();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <View>
      <Text>{results.join('\n')}</Text>
      <Button title="Start" onPress={start} />
      <Button title="Stop" onPress={stop} />
    </View>
  );
}
```

---

## Real-Time Audio Streaming

For voice assistants or real-time audio processing, use `expo-audio-stream`.

```bash
npm install expo-audio-stream
npx expo prebuild --clean
```

```typescript
import { ExpoAudioStreamModule } from 'expo-audio-stream';

const startStreaming = async () => {
  await ExpoAudioStreamModule.startRecording({
    sampleRate: 16000,
    channelConfig: 'mono',
    audioFormat: 'pcm_16bit',
    onAudioStream: (audioData) => {
      // Process audio chunk
      // Send to speech API, etc.
    },
  });
};

const stopStreaming = async () => {
  await ExpoAudioStreamModule.stopRecording();
};
```

---

## Platform Comparison

| Feature | iOS | Android | Expo Go |
|---------|-----|---------|---------|
| Audio playback | ✅ | ✅ | ✅ |
| Audio recording | ✅ | ✅ | ✅ |
| Text-to-speech | ✅ | ✅ | ✅ |
| Speech recognition | ✅ | ✅ | ❌ |
| On-device STT | iOS 13+ | Android 10+ | ❌ |
| Background audio | ✅ (config) | ✅ | ❌ |

---

## Complete Voice Assistant Example

```typescript
import * as Speech from 'expo-speech';
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from '@jamsch/expo-speech-recognition';
import { useState, useCallback } from 'react';

export function VoiceAssistant() {
  const [isListening, setIsListening] = useState(false);
  const [userSpeech, setUserSpeech] = useState('');
  const [response, setResponse] = useState('');

  useSpeechRecognitionEvent('result', (event) => {
    const text = event.results[0]?.transcript || '';
    setUserSpeech(text);
    
    // Final result - process and respond
    if (event.results[0]?.isFinal) {
      processCommand(text);
    }
  });

  useSpeechRecognitionEvent('end', () => {
    setIsListening(false);
  });

  const processCommand = useCallback(async (command: string) => {
    // Simple command processing
    let reply = '';
    
    if (command.toLowerCase().includes('hello')) {
      reply = 'Hello! How can I help you?';
    } else if (command.toLowerCase().includes('time')) {
      reply = `The time is ${new Date().toLocaleTimeString()}`;
    } else {
      reply = `You said: ${command}`;
    }
    
    setResponse(reply);
    Speech.speak(reply);
  }, []);

  const startListening = async () => {
    const { granted } = await ExpoSpeechRecognitionModule.requestPermissionsAsync();
    if (!granted) return;

    setIsListening(true);
    setUserSpeech('');
    
    ExpoSpeechRecognitionModule.start({
      lang: 'en-US',
      interimResults: true,
    });
  };

  return (
    <View style={{ flex: 1, padding: 20, justifyContent: 'center' }}>
      <Text style={{ fontSize: 16, color: 'gray' }}>You said:</Text>
      <Text style={{ fontSize: 20, marginBottom: 20 }}>{userSpeech}</Text>
      
      <Text style={{ fontSize: 16, color: 'gray' }}>Response:</Text>
      <Text style={{ fontSize: 20, marginBottom: 40 }}>{response}</Text>
      
      <TouchableOpacity
        onPress={startListening}
        disabled={isListening}
        style={{
          width: 100,
          height: 100,
          borderRadius: 50,
          backgroundColor: isListening ? 'red' : 'blue',
          alignSelf: 'center',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Text style={{ color: 'white', fontSize: 16 }}>
          {isListening ? 'Listening...' : 'Tap to Speak'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}
```
