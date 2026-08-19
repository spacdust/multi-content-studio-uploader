---
name: content-uploader
description: "Automated content uploader for TikTok and Instagram Reels/Posts using Playwright browser automation, intelligent sound/audio mixing, and queue management."
version: 1.1.0
author: Content Uploader Team
license: MIT
platforms: [windows, linux, macos]
prerequisites:
  commands: [python, ffmpeg]
metadata:
  hermes:
    tags: [social-media, tiktok, instagram, reels, video-upload, sound-mixing, audio-volume, queue-automation]
---

# Content Uploader — TikTok & Instagram Automation Skill

This skill allows the agent to check social media login sessions, upload videos directly to TikTok and Instagram (Reels & Posts), adjust sound volume, add background music (BGM), manage the upload queue, and generate optimized captions and hashtags.

**Root Workspace Directory:** `C:\Users\spacdust\Desktop\DEV\Bot\content-uploader`

---

## 1. Sound Selection & Volume Presets

Before uploading, you can inspect available sounds and presets:
```powershell
python -m src.cli sound list
```

### Available Volume Presets (`--preset`):
* `voiceover`: Original audio 100%, background music 15% (Ideal for tutorials, voiceovers, vlogs).
* `balanced`: Original audio 100%, background music 25% (Standard balanced social media post).
* `music_beat`: Original audio 30%, background music 100% (Cinematic, gameplay, music trends).
* `mute_original`: Original audio 0%, background music 100% (Mutes original sound completely).
* `boost_voice`: Original audio 150%, background music 12% (Boosts quiet speaking voices).

---

## 2. Authentication & Status Commands

Verify if login sessions are active:
```powershell
python -m src.cli check-auth --platform all
```

If not logged in:
```powershell
python -m src.cli login --platform all
```

---

## 3. Direct Upload with Sound & Volume Controls

### Upload with Preset Sound Balance
```powershell
python -m src.cli upload --video "C:/path/to/video.mp4" --caption "Tutorial coding #fyp" --preset voiceover --sound "bgm.mp3" --platform all
```

### Upload with Custom Volumes (e.g. 80% Original, 20% Music)
```powershell
python -m src.cli upload --video "C:/path/to/video.mp4" --caption "Keseruan hari ini #vlog" --original-volume 0.8 --music-volume 0.2 --sound "assets/sounds/ambient.mp3" --platform all
```

### Upload to TikTok Only (or Draft)
```powershell
python -m src.cli upload --video "C:/path/to/video.mp4" --caption "TikTok post" --platform tiktok
```

### Upload to Instagram Only
```powershell
python -m src.cli upload --video "C:/path/to/video.mp4" --caption "Reel post" --platform instagram
```

---

## 4. Queue Pipeline Commands

The queue is located at `C:\Users\spacdust\Desktop\DEV\Bot\content-uploader\queue\`.

### List Queue
```powershell
python -m src.cli queue list
```

### Add to Queue with Sound Settings
```powershell
python -m src.cli queue add --video "C:/path/to/video.mp4" --caption "Batch upload video" --preset balanced --sound "chill_beat.mp3" --platform all
```

### Process Queue
```powershell
python -m src.cli queue process --platform all
```
