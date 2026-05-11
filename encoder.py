import os, sys, time, asyncio, json, base64, shutil
import pyrogram.utils

def patched_get_peer_type(peer_id: int) -> str:
    val = str(peer_id)
    if val.startswith("-100"): return "channel"
    elif val.startswith("-"): return "chat"
    else: return "user"

pyrogram.utils.get_peer_type = patched_get_peer_type

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

TASK_TYPE = os.getenv("TASK_TYPE")
VIDEO_ID = os.getenv("VIDEO_ID")
SUB_ID = os.getenv("SUB_ID")
RENAME = os.getenv("RENAME", "output.mp4")
CHAT_ID = int(os.getenv("CHAT_ID"))
THREAD_ID = os.getenv("THREAD_ID")

raw_dump = os.getenv("DUMP_ID", "none")
STATUS_MSG_ID = None
RESOLUTION = "original"
USER_SETTINGS = {}

if ":::" in raw_dump:
    parts = raw_dump.split(":::")
    DUMP_ID = parts[0]
    LOGO_ID = parts[1]
    if len(parts) > 2: STATUS_MSG_ID = parts[2]
    if len(parts) > 3: RESOLUTION = parts[3]
    if len(parts) > 4:
        try: 
            # 100% Unbreakable Base64 Decoding
            b64_str = parts[4]
            pad = len(b64_str) % 4
            if pad: b64_str += "=" * (4 - pad)
            USER_SETTINGS = json.loads(base64.urlsafe_b64decode(b64_str).decode('utf-8'))
        except Exception as e: 
            print("Failed to decode settings:", e)
else:
    DUMP_ID = raw_dump
    LOGO_ID = "none"

last_edit_time = 0

def get_readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    if int(days) != 0: result += f"{int(days)}d "
    (hours, remainder) = divmod(remainder, 3600)
    if int(hours) != 0: result += f"{int(hours)}h "
    (minutes, seconds) = divmod(remainder, 60)
    if int(minutes) != 0: result += f"{int(minutes)}m "
    result += f"{int(seconds)} sec"
    return result.strip()

async def get_duration(file_path):
    cmd =['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    stdout, _ = await proc.communicate()
    try: return float(stdout.decode().strip())
    except: return 0.0

async def progress_bar(current, total, app, msg_id, action_text):
    global last_edit_time
    now = time.time()
    if now - last_edit_time > 5 or current == total:
        try:
            perc = (current / total) * 100 if total > 0 else 0
            bar_length = 14
            filled = int((perc / 100) * bar_length)
            bar = "▓" * filled + "░" * (bar_length - filled)
            
            cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_cloud_task_cloud")]])
            text = (
                f"🎬  GITHUB WORKER \n"
                "──────────────────────────\n"
                f"📦 File     : `{RENAME}`\n"
                f"▸ Status    : {action_text}\n"
                f"▸ Progress  : {bar}  {perc:.1f}%\n"
                f"▸ Size      : {current/(1024*1024):.1f} MB / {total/(1024*1024):.1f} MB\n"
                "──────────────────────────\n"
                "⚙ Running on Cloud Engine"
            )
            await app.edit_message_text(CHAT_ID, msg_id, text, reply_markup=cancel_kb)
            last_edit_time = now
        except: pass

async def download_phase():
    app = Client("worker_down", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await app.start()
    
    cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_cloud_task_cloud")]])
    
    if STATUS_MSG_ID:
        msg_id = int(STATUS_MSG_ID)
        try: await app.edit_message_text(CHAT_ID, msg_id, f"⚙️ Worker Triggered: Preparing...\n📦 File: `{RENAME}`", reply_markup=cancel_kb)
        except:
            status_msg = await app.send_message(CHAT_ID, f"⚙️ Worker Triggered: Preparing...\n📦 File: `{RENAME}`", reply_markup=cancel_kb)
            msg_id = status_msg.id
    else:
        status_msg = await app.send_message(CHAT_ID, f"⚙️ Worker Triggered: Preparing...\n📦 File: `{RENAME}`", reply_markup=cancel_kb)
        msg_id = status_msg.id
    
    # SAFEST Renaming to Avoid FFmpeg Crashes on Special Characters!
    orig_vid = await app.download_media(VIDEO_ID, progress=progress_bar, progress_args=(app, msg_id, "📥 Downloading Video"))
    if not orig_vid:
        await app.edit_message_text(CHAT_ID, msg_id, "❌ **Error:** Failed to download video from Telegram.")
        await app.stop()
        return None, None, None, msg_id
        
    ext = os.path.splitext(orig_vid)[1]
    video_path = f"safe_vid{ext}"
    if os.path.exists(video_path): os.remove(video_path)
    shutil.move(orig_vid, video_path)

    sub_path = None
    if TASK_TYPE == "hardsub" and SUB_ID != "none":
        orig_sub = await app.download_media(SUB_ID, progress=progress_bar, progress_args=(app, msg_id, "📥 Downloading Subtitle"))
        if orig_sub:
            ext = os.path.splitext(orig_sub)[1]
            sub_path = f"safe_sub{ext}"
            if os.path.exists(sub_path): os.remove(sub_path)
            shutil.move(orig_sub, sub_path)
            
    logo_path = None
    if TASK_TYPE == "hardsub" and LOGO_ID != "none":
        orig_logo = await app.download_media(LOGO_ID, progress=progress_bar, progress_args=(app, msg_id, "📥 Downloading Logo"))
        if orig_logo:
            ext = os.path.splitext(orig_logo)[1]
            logo_path = f"safe_logo{ext}"
            if os.path.exists(logo_path): os.remove(logo_path)
            shutil.move(orig_logo, logo_path)
            
    await app.edit_message_text(CHAT_ID, msg_id, f"🔥 Starting FFmpeg Engine...\n📦 File: `{RENAME}`\n*(Connection Paused for Safety)*", reply_markup=cancel_kb)
    await app.stop() 
    return video_path, sub_path, logo_path, msg_id

async def encode_phase(video_path, sub_path, logo_path, msg_id):
    if not video_path: return None, 1
    output = RENAME
    duration = await get_duration(video_path)
    os.makedirs("fonts", exist_ok=True)
    
    # Safe Defaults & Parsing
    crf = USER_SETTINGS.get('crf') or '22'
    preset = USER_SETTINGS.get('preset') or 'slow'
    codec = USER_SETTINGS.get('codec') or 'libx264'
    audiocodec = USER_SETTINGS.get('audiocodec') or 'copy'
    audio_bitrate = USER_SETTINGS.get('audio')
    tune = USER_SETTINGS.get('tune')
    bit_depth = USER_SETTINGS.get('bit')
    fps = USER_SETTINGS.get('fps')
    
    crf = str(crf).split()[0]
    preset = str(preset).split()[0]
    codec = str(codec).split()[0]
    audiocodec = str(audiocodec).split()[0]
    
    v_args = ['-c:v', codec, '-preset', preset]
    if codec != 'copy':
        v_args.extend(['-crf', crf])
        if tune and tune != "None": v_args.extend(['-tune', str(tune).split()[0]])
        if bit_depth and '10bit' in str(bit_depth): v_args.extend(['-pix_fmt', 'yuv420p10le'])
        elif bit_depth and '8bit' in str(bit_depth): v_args.extend(['-pix_fmt', 'yuv420p'])
        if fps and fps != "Original": v_args.extend(['-r', str(fps).split()[0]])
        
    a_args = ['-c:a', audiocodec]
    if audio_bitrate and audiocodec != 'copy':
        a_args.extend(['-b:a', str(audio_bitrate).split()[0]])
    
    if TASK_TYPE == "hardsub":
        # Guaranteed no special characters in path
        sub_filter = f"subtitles='{sub_path}':fontsdir='fonts'" if sub_path else ""

        if logo_path:
            scale_val = "120:-1"
            pos_val = "main_w-overlay_w-15:15"
            filter_complex = f"[1:v]scale={scale_val}[logo];[0:v]{sub_filter}[subbed];[subbed][logo]overlay={pos_val}" if sub_filter else f"[1:v]scale={scale_val}[logo];[0:v][logo]overlay={pos_val}"
            cmd = ['ffmpeg', '-y', '-i', video_path, '-i', logo_path, '-filter_complex', filter_complex, '-map', '0:a?', '-sn'] + v_args + a_args + ['-progress', 'pipe:1', output]
        else:
            if sub_filter:
                cmd = ['ffmpeg', '-y', '-i', video_path, '-map', '0:v:0', '-map', '0:a?', '-sn', '-vf', sub_filter] + v_args + a_args + ['-progress', 'pipe:1', output]
            else:
                cmd = ['ffmpeg', '-y', '-i', video_path, '-map', '0:v:0', '-map', '0:a?', '-sn'] + v_args + a_args + ['-progress', 'pipe:1', output]
        engine_name = "HARDSUB ENGINE"
    else:
        if RESOLUTION != "original":
            vf_scale = f"scale=-2:{RESOLUTION}"
            cmd = ['ffmpeg', '-y', '-i', video_path, '-map', '0:v:0', '-map', '0:a?', '-sn', '-vf', vf_scale] + v_args + a_args + ['-progress', 'pipe:1', output]
        else:
            cmd = ['ffmpeg', '-y', '-i', video_path, '-map', '0:v:0', '-map', '0:a?', '-sn'] + v_args + a_args + ['-progress', 'pipe:1', output]
        engine_name = "COMPRESSION ENGINE"

    app = Client("worker_enc", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await app.start()
    
    with open("ffmpeg_error.log", "w") as err_file:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=err_file)
        
    start_time = time.time()
    last_up = 0

    while True:
        line = await proc.stdout.readline()
        if not line: break
        line = line.decode('utf-8').strip()
        if line.startswith('out_time_us='):
            try:
                time_str = line.split('=')[1]
                if time_str.lower() == 'n/a': continue 
                cur = int(time_str) / 1000000
                now = time.time()
                
                if (now - last_up) > 10:
                    if duration > 0:
                        perc = min(100, (cur / duration) * 100)
                        elapsed = now - start_time
                        speed = cur / elapsed if elapsed > 0 else 0
                        eta = (duration - cur) / speed if speed > 0 else 0
                        bar_length = 14
                        filled = int((perc / 100) * bar_length)
                        bar = "▓" * filled + "░" * (bar_length - filled)
                        prog_text = f"▸ Progress  : {bar}  {perc:.2f}%\n▸ Velocity  : {speed:.2f}x\n▸ Remaining : ~{get_readable_time(eta)}"
                    else:
                        prog_text = f"▸ Processed : {get_readable_time(cur)}\n▸ Duration  : Unknown"
                        
                    cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_cloud_task_cloud")]])
                    text = (
                        f"🎬  {engine_name} \n"
                        "──────────────────────────\n"
                        f"📦 File     : `{RENAME}`\n"
                        f"▸ Status    : Processing Frame...\n"
                        f"{prog_text}\n"
                        "──────────────────────────\n"
                        "⚙ GitHub Cloud Worker"
                    )
                    try: await app.edit_message_text(CHAT_ID, msg_id, text, reply_markup=cancel_kb)
                    except: pass
                    last_up = now
            except: pass
            
    await proc.wait()
    await app.stop()
    return output, proc.returncode

async def extract_thumbnail(video_path, thumb_path):
    cmd =['ffmpeg', '-y', '-ss', '00:00:05', '-i', video_path, '-vf', 'scale=320:-1', '-vframes', '1', thumb_path]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.communicate()
    return os.path.exists(thumb_path)

async def upload_phase(output, returncode, msg_id):
    if not output or not msg_id: return
    app = Client("worker_up", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await app.start()
    
    if returncode == 0 and os.path.exists(output):
        thumb_path = "thumb.jpg"
        has_thumb = await extract_thumbnail(output, thumb_path)
        
        await app.edit_message_text(CHAT_ID, msg_id, f"▸ Processing Done! Starting Fresh Upload...\n📦 File: `{RENAME}`")
        
        target_chat = int(DUMP_ID) if DUMP_ID != "none" else CHAT_ID
        thread = int(THREAD_ID) if THREAD_ID != "none" else None
        cap = f"✅ {TASK_TYPE.upper()} COMPLETE\n📦 File: `{RENAME}`"
        
        try:
            await app.send_document(
                chat_id=target_chat, document=output, reply_to_message_id=thread,
                thumb=thumb_path if has_thumb else None, caption=cap,
                progress=progress_bar, progress_args=(app, msg_id, "📤 Uploading Video")
            )
            if target_chat != CHAT_ID:
                await app.send_message(CHAT_ID, f"{cap}\n\nFile successfully sent to your PM / Dump Group!")
            await app.delete_messages(CHAT_ID, msg_id)
        except Exception as e:
            await app.edit_message_text(CHAT_ID, msg_id, f"❌ Upload Error: {str(e)}")
    else:
        err_msg = "Unknown Reason"
        if os.path.exists("ffmpeg_error.log"):
            with open("ffmpeg_error.log", "r") as f:
                err_msg = "".join(f.readlines()[-15:])[-1000:]
        await app.edit_message_text(CHAT_ID, msg_id, f"❌ **FFmpeg Error:** Failed to Process Video.\n\n**Log:**\n`{err_msg}`")
    
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    vid, sub, logo, mid = loop.run_until_complete(download_phase())
    if vid:
        out, rcode = loop.run_until_complete(encode_phase(vid, sub, logo, mid))
        loop.run_until_complete(upload_phase(out, rcode, mid))
