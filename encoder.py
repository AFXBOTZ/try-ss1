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
            req = Processed : {get_readable_time(cur)}\n▸ Duration  : Unknown"
                                
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
                if USER_ID:
                    cap += f"\n👤 **Requested By:** [User](tg://user?id={USER_ID})"
                
                try:
                    await app.send_document(
                        chat_id=target_chat, document=output, reply_to_message_id=thread,
                        thumb=thumb_path if has_thumb else None, caption=cap,
                        progress=progress_bar, progress_args=(app, msg_id, "📤 Uploading Video")
                    )
                    
                    if target_chat != CHAT_ID:
                        tag_text = f"\n👤 [User](tg://user?id={USER_ID})" if USER_ID else ""
                        await app.send_message(CHAT_ID, f"{cap}\n\nFile successfully sent to your Dump Group!{tag_text}")
                        
                    await app.delete_messages(CHAT_ID, msg_id)
                except Exception as e:
                    await send_error_to_telegram(app, msg_id, f"Upload Error:\n{traceback.format_exc()}")
            else:
                err_msg = "Unknown Reason"
                if os.path.exists("ffmpeg_error.log"):
                    with open("ffmpeg_error.log", "r") as f:
                        err_msg = "".join(f.readlines()[-15:])[-1000:]
                await send_error_to urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
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
    USER_ID = ""

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
        if len(parts) > 5:
            USER_ID = parts[5]

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
        cmd =_telegram(app, msg_id, f"FFmpeg Encode Failed:\n{err_msg}")

        except Exception as e:
            await send_error_to_telegram(app, msg_id, f"Fatal Worker Crash:\n{traceback.format_exc()}")
        finally:
            await app.stop()

    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_all())

except Exception as e:
    emergency_alert(traceback.format_exc())
