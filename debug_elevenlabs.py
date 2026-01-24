try:
    import elevenlabs
    from elevenlabs import play
    print(f"ElevenLabs Version: {getattr(elevenlabs, '__version__', 'Unknown')}")
    print(f"Type of 'play': {type(play)}")
    print(f"Dir of 'play': {dir(play)}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
