import os
import asyncio
import pyaudio
from speechmatics.rt import AsyncClient

# Paste your actual key here
TOKEN = "UTbS7EpU8neWgepXbnld3Tw21cgf3NmH"

async def main():
    # In version 1.0.0, we pass the token and URL directly to the client
    client = AsyncClient(
        auth_token=TOKEN,
        url="wss://stream.api.speechmatics.com/v2"
    )
    
    # Configure parameters for the connection
    conf = {
        "language": "en",
        "type": "transcription",
        "transcription_config": {"operating_point": "enhanced"}
    }

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

    print("\n[Voice Gateway Open] 🎙️ MIC IS LIVE! Describe cargo damage, then press Ctrl+C...")

    # The 1.0.0 SDK uses a simple context manager for the connection
    async with client as session:
        # Start the transcription
        await session.start(conf)
        
        # Define the audio loop
        async def send_audio():
            while True:
                data = stream.read(1024, exception_on_overflow=False)
                await session.send_audio(data)
                await asyncio.sleep(0.01)

        # Define the message handler loop
        async def receive_messages():
            async for msg in session:
                if msg.get("message") == "AddTranscript":
                    print(f"[Live Text]: {msg.get('metadata', {}).get('transcript', '')}")

        try:
            # Run both tasks concurrently
            await asyncio.gather(send_audio(), receive_messages())
        except asyncio.CancelledError:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[System] Stream stopped.")