import os, sys, time, asyncio, json, base64, shutil, traceback, ast
import urllib.request

# 🚨 GUARANTEED EMERGENCY ALERT SYSTEM 🚨
_chat_id_str = os.getenv("CHAT_ID", "0").strip()
_raw_dump = os.getenv("DUMP_ID", "none")
_bot_token = os.getenv("BOT_TOKEN", "").strip()

if ":::" in _raw_dump:
    parts = _raw_dump.split(":::")
    if len(parts) > 4:
        try:
            raw_set = parts[4]
            pad = len(raw_set) % 4
            if pad: raw_set += "=" * (4 - pad)
            _settings = json.loads(base64.urlsafe_b64decode(raw_set).decode('utf-8'))
            _bot_token = _settings.get('__bot_token', _bot_token)
        except: pass

def emergency_alert(msg):
    if _bot_token and _chat_id_str != "0" and _chat_id_str != "none":
        try:
            url = f"https://api.telegram.org/bot{_bot_token}/sendMessage"
            payload = {"chat_id": _chat_id_str, "text": f"🚨 **GITHUB WORKER CRASHED:**\n\n`{msg[-2000:]}`", "parse_mode": "Markdown"}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
        except: pass

try:
    import pyrogram.utils

    def patched_get_peer_type(peer_id: int) -> str:
        val = str(peer_id)
        if val.startswith("-100"): return "channel"
        elif val.startswith("-"): return "chat"
        else: return "user"

    pyrogram.utils.get_peer_type = patched_get_peer_type

    from pyrogram import Client
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    API_ID_STR = os.getenv("API_ID", "0").strip()
    API_ID = int(API_ID_STR) if API_ID_STR.isdigit() else 0
    API_HASH = os.getenv("API_HASH", "").strip()
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

    TASK_TYPE = os.getenv("TASK_TYPE", "hardsub")
    VIDEO_ID = os.getenv("VIDEO_ID", "")
    SUB_ID = os.getenv("SUB_ID", "none")
    RENAME = os.getenv("RENAME", "output.mp4")
    CHAT_ID_STR = os.getenv("CHAT_ID", "0")
    CHAT_ID = int(CHAT_ID_STR) if CHAT_ID_STR.lstrip('-').isdigit() else 0
    THREAD_ID = os.getenv("THREAD_ID", "none")

    STATUS_MSG_ID = None
    RESOLUTION = "original"
    USER_SETTINGS = {}

    DUMP_ID = _raw_dump
    LOGO_ID = "none"

    if ":::" in _raw_dump:
        parts = _raw_dump.split(":::")
        DUMP_ID = parts[0]
        LOGO_ID = parts[1]
        if len(parts) > 2: STATUS_MSG_ID = parts[2]
        if len(parts) > 3: RESOLUTION = parts[3]
        if len(parts) > 4:
            try: 
                raw_set = parts[4]
                pad = len(raw_set) % 4
                if pad: raw_set += "=" * (4 - pad)
                USER_SETTINGS = json.loads(base64.urlsafe_b64decode(raw_set).decode('utf-8'))
            except:
                try: USER_SETTINGS = ast.literal_eval(parts[4])
                except: pass

    # Override keys with the Payload sent from Hugging Face
    API_ID = int(USER_SETTINGS.get('__api_id', API_ID))
    API_HASH = USER_SETTINGS.get('__api_hash', API_HASH)
    BOT_TOKEN = USER_SETTINGS.get('__bot_token', BOT_TOKEN)

    if API_ID == 0 or not API_HASH or not BOT_TOKEN:
        raise ValueError("GitHub Credentials missing! Could not retrieve API_ID or BOT_TOKEN.")

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

    async def send_error_to_telegram(app, msg_id, error_msg):
        try:
            await app.edit_message_text(CHAT_ID, msg_id, f"❌ **Cloud Worker Error:**\n\n`{error_msg[-1000:]}`")
        except:
            try: await app.send_message(CHAT_ID, f"❌ **Cloud Worker Error:**\n\n`{error_msg[-1000:]}`")
            except: pass

    async def process_all():
        app = Client("worker_down", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
        await app.start()
        
        cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_cloud_task_cloud")]])
        msg_id = None
        
        if STATUS_MSG_ID and STATUS_MSG_ID.isdigit():
            msg_id = int(STATUS_MSG_ID)
            try: await app.edit_message_text(CHAT_ID, msg_id, f"⚙️ Worker Triggered: Preparing...\n📦 File: `{RENAME}`", reply_markup=cancel_kb)
            except:
                status_msg = await app.send_message(CHAT_ID, f"⚙️ Worker Triggered: Preparing...\n📦 File: `{RENAME}`", reply_markup=cancel_kb)
                msg_id = status_msg.id
        else:
            status_msg = await app.send_message(CHAT_ID, f"⚙️ Worker Triggered: Preparing...\n📦 File: `{RENAME}`", reply_markup=cancel_kb)
            msg_id = status_msg.id

        try:
            # == PHASE 1: DOWNLOAD ==
            try:
                orig_vid = await app.download_media(VIDEO_ID, progress=progress_bar, progress_args=(app, msg_id, "📥 Downloading Video"))
                if not orig_vid:
                    await send_error_to_telegram(app, msg_id, "Video download failed (Reference Expired). Please restart task.")
                    await app.stop()
                    return
                
                ext = os.path.splitext(orig_vid)[1]
                video_path = f"safe_vid{ext}"
                if os.path.exists(video_path): os.remove(video_path)
                shutil.move(orig_vid, video_path)
            except Exception as e:
                await send_error_to_telegram(app, msg_id, f"Video Download Error:\n{traceback.format_exc()}")
                await app.stop()
                return

            sub_path = None
            if TASK_TYPE == "hardsub" and SUB_ID != "none":
                try:
                    orig_sub = await app.download_media(SUB_ID, progress=progress_bar, progress_args=(app, msg_id, "📥 Downloading Subtitle"))
                    if orig_sub:
                        ext = os.path.splitext(orig_sub)[1]
                        sub_path = f"safe_sub{ext}"
                        if os.path.exists(sub_path): os.remove(sub_path)
                        shutil.move(orig_sub, sub_path)
                except Exception as e:
                    await send_error_to_telegram(app, msg_id, f"Subtitle Download Error:\n{traceback.format_exc()}")
                    await app.stop()
                    return
                    
            logo_path = None
            if TASK_TYPE == "hardsub" and LOGO_ID != "none":
                try:
                    orig_logo = await app.download_media(LOGO_ID, progress=progress_bar, progress_args=(app, msg_id, "📥 Downloading Logo"))
                    if orig_logo:
                        ext = os.path.splitext(orig_logo)[1]
                        logo_path = f"safe_logo{ext}"
                        if os.path.exists(logo_path): os.remove(logo_path)
                        shutil.move(orig_logo, logo_path)
                except: pass

            await app.edit_message_text(CHAT_ID, msg_id, f"🔥 Starting FFmpeg Engine...\n📦 File: `{RENAME}`", reply_markup=cancel_kb)
            
            # == PHASE 2: ENCODE ==
            output = RENAME
            duration = await get_duration(video_path)
            os.makedirs("fonts", exist_ok=True)
            
            crf = USER_SETTINGS.get('crf', '22')
            preset = USER_SETTINGS.get('preset', 'slow')
            codec = USER_SETTINGS.get('codec', 'libx264')
            audiocodec = USER_SETTINGS.get('audiocodec', 'copy')
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
                sub_filter = f"subtitles={sub_path}:fontsdir=fonts" if sub_path else ""

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
            
            # == PHASE 3: UPLOAD ==
            if proc.returncode == 0 and os.path.exists(output):
                thumb_path = "thumb.jpg"
                cmd_thumb = ['ffmpeg', '-y', '-ss', '00:00:05', '-i', output, '-vf', 'scale=320:-1', '-vframes', '1', thumb_path]
                t_proc = await asyncio.create_subprocess_exec(*cmd_thumb, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await t_proc.wait()
                has_thumb = os.path.exists(thumb_path)
                
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
                    await send_error_to_telegram(app, msg_id, f"Upload Error:\n{traceback.format_exc()}")
            else:
                err_msg = "Unknown Reason"
                if os.path.exists("ffmpeg_error.log"):
                    with open("ffmpeg_error.log", "r") as f:
                        err_msg = "".join(f.readlines()[-15:])[-1000:]
                await send_error_to_telegram(app, msg_id, f"FFmpeg Encode Failed:\n{err_msg}")

        except Exception as e:
            await send_error_to_telegram(app, msg_id, f"Fatal Worker Crash:\n{traceback.format_exc()}")
        finally:
            await app.stop()

    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_all())

except Exception as e:
    emergency_alert(traceback.format_exc())
