import os
import asyncio
import logging
import re
from io import BytesIO
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- PYTHON 3.14+ (EVENT LOOP) UYUMLULUK YAMASI ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# --------------------------------------------------

from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio

logging.getLogger("pyrogram").setLevel(logging.CRITICAL)

# --- RENDER'I UYANIK TUTMAK İÇİN MİNİ WEB SUNUCUSU ---
class SaglikKontrolu(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Userbot aktif ve log tutuyor!".encode("utf-8"))
        
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        
    def log_message(self, format, *args):
        return 

def web_sunucusunu_baslat():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SaglikKontrolu)
    server.serve_forever()

Thread(target=web_sunucusunu_baslat, daemon=True).start()
# -----------------------------------------------------

# --- GİZLİ KEYLERİ SUNUCUDAN ÇEKME ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
STRING_SESSION = os.environ.get("STRING_SESSION")

KAYNAK_GRUP_ID = int(os.environ.get("KAYNAK_GRUP_ID"))
KAYNAK_KONU = int(os.environ.get("KAYNAK_KONU"))

YEDEK_GRUP_ID = int(os.environ.get("YEDEK_GRUP_ID"))
YEDEK_KONU = int(os.environ.get("YEDEK_KONU"))

# ESKİ LOG KONUSU
LOG_KONU = 78582
# YENİ EKLENEN İNDİRME LOG KONUSU
YENI_LOG_KONU = 93842

# EKSTRA KANALLAR/GRUPLAR (Opsiyonel)
KAYNAK_IDLER = []
for key, value in os.environ.items():
    if key.startswith("KAYNAK_ID"):
        try:
            KAYNAK_IDLER.append(int(value.strip()))
        except ValueError:
            pass

TUM_KAYNAKLAR = [KAYNAK_GRUP_ID] + KAYNAK_IDLER
# -------------------------------------

def susturucu(hata_loop, context):
    hata_metni = str(context.get("exception", ""))
    if "Peer id invalid" in hata_metni or "ID not found" in hata_metni:
        pass 
    else:
        hata_loop.default_exception_handler(context)

loop.set_exception_handler(susturucu)

app = Client("benim_userbotum", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

album_havuzu = {}

def ram_dosyasini_isimlendir(msg, ram_dosyasi):
    if msg.photo: ram_dosyasi.name = "gorsel.jpg"
    elif msg.video: ram_dosyasi.name = "video.mp4"
    elif msg.voice: ram_dosyasi.name = "ses_kaydi.ogg"
    elif msg.audio: ram_dosyasi.name = getattr(msg.audio, "file_name", "muzik.mp3")
    elif msg.video_note: ram_dosyasi.name = "yuvarlak_video.mp4"
    elif msg.document: ram_dosyasi.name = getattr(msg.document, "file_name", "belge.file")
    else: ram_dosyasi.name = "bilinmeyen_dosya.dat"
    return ram_dosyasi

# ==========================================
# YENİ ÖZELLİK: MANUEL VE TOPLU İNDİRME (.indir)
# ==========================================
@app.on_message(filters.command("indir", prefixes=".") & filters.me)
async def manuel_linkten_indir(client, message):
    try:
        durum_mesaji = await message.edit_text("⏳ Sistem yanit verdi, linkler taraniyor...")
        
        text_to_search = message.text or ""
        if message.reply_to_message:
            text_to_search += " " + (message.reply_to_message.text or message.reply_to_message.caption or "")
            
        links = re.findall(r'https://t\.me/(?:c/)?[a-zA-Z0-9_/-]+', text_to_search)
        links = list(dict.fromkeys([link.split("?")[0].rstrip("/") for link in links]))
        
        if not links:
            await durum_mesaji.edit_text("❌ Kullanim: .indir https://t.me/...")
            return

        await durum_mesaji.edit_text(f"⏳ Toplu indirme baslatiliyor... Toplam Link: {len(links)}")
        
        hedef_chat = message.chat.id
        hedef_konu = getattr(message, "message_thread_id", None)
        if not hedef_konu and message.reply_to_message:
            hedef_konu = getattr(message.reply_to_message, "message_thread_id", None) or message.reply_to_message.id
        if not hedef_konu:
            hedef_konu = message.id
        
        basarili = 0
        hatali = 0
        
        for i, link in enumerate(links, 1):
            try:
                await durum_mesaji.edit_text(f"⏳ Indiriliyor ({i}/{len(links)})...")
                parts = link.split("/")
                msg_id = int(parts[-1])
                chat_id = int("-100" + parts[-2]) if "c" in parts else parts[-2]
                    
                try:
                    msg = await client.get_messages(chat_id, msg_id)
                except Exception as e:
                    if "Peer id invalid" in str(e).capitalize() or "PEER_ID_INVALID" in str(e):
                        await durum_mesaji.edit_text(f"⏳ Gizli kanal icin onbellek yenileniyor ({i}/{len(links)})...")
                        async for _ in client.get_dialogs(limit=300): pass
                        msg = await client.get_messages(chat_id, msg_id)
                    else: raise e
                
                if not msg or msg.empty or not getattr(msg, "media", None):
                    hatali += 1
                    continue

                if getattr(msg, "media_group_id", None):
                    try:
                        album_mesajlari = await client.get_media_group(chat_id, msg_id)
                    except Exception as e:
                        if "Peer id invalid" in str(e).capitalize() or "PEER_ID_INVALID" in str(e):
                            async for _ in client.get_dialogs(limit=300): pass
                            album_mesajlari = await client.get_media_group(chat_id, msg_id)
                        else: raise e

                    medya_grubu = []
                    for m in album_mesajlari:
                        ram_dosyasi = await client.download_media(m, in_memory=True)
                        ram_dosyasi = ram_dosyasini_isimlendir(m, ram_dosyasi)
                        
                        if m.photo: medya_grubu.append(InputMediaPhoto(media=ram_dosyasi))
                        elif m.video: medya_grubu.append(InputMediaVideo(media=ram_dosyasi))
                        elif m.document: medya_grubu.append(InputMediaDocument(media=ram_dosyasi))
                        elif m.audio: medya_grubu.append(InputMediaAudio(media=ram_dosyasi))
                    if medya_grubu:
                        await client.send_media_group(chat_id=hedef_chat, media=medya_grubu, reply_to_message_id=hedef_konu)
                else:
                    ram_dosyasi = await client.download_media(msg, in_memory=True)
                    ram_dosyasi = ram_dosyasini_isimlendir(msg, ram_dosyasi)
                    
                    if msg.photo: await client.send_photo(chat_id=hedef_chat, photo=ram_dosyasi, reply_to_message_id=hedef_konu)
                    elif msg.video: await client.send_video(chat_id=hedef_chat, video=ram_dosyasi, reply_to_message_id=hedef_konu)
                    elif msg.audio or msg.voice: await client.send_audio(chat_id=hedef_chat, audio=ram_dosyasi, reply_to_message_id=hedef_konu)
                    elif msg.document: await client.send_document(chat_id=hedef_chat, document=ram_dosyasi, reply_to_message_id=hedef_konu)
                    elif msg.video_note: await client.send_video_note(chat_id=hedef_chat, video_note=ram_dosyasi, reply_to_message_id=hedef_konu)
                
                basarili += 1
                await asyncio.sleep(2) 
            except Exception as e:
                hatali += 1
                
        await durum_mesaji.edit_text(f"✅ Islem Tamamlandi!\n📥 Indirilen: {basarili} | ❌ Hatali: {hatali}")
    except Exception as master_error:
        print(f"Kritik Komut Hatası: {master_error}")

# ==========================================
# ANA OTO-İLET SİSTEMİ
# ==========================================
async def albumu_isle_ve_yolla(client, grup_id):
    await asyncio.sleep(2) 
    mesajlar = album_havuzu.pop(grup_id, None)
    if not mesajlar: return

    gonderen = mesajlar[0].from_user
    kaynak_id = mesajlar[0].chat.id

    if gonderen:
        if gonderen.username:
            kisi_linki = f"@{gonderen.username}"
        else:
            isim = gonderen.first_name or "Bilinmeyen İsim"
            kisi_linki = f"[{isim}](tg://user?id={gonderen.id})"
    else:
        kisi_linki = "Gizli/Bilinmeyen Kullanıcı"

    try:
        # --- A. ORİJİNAL KODUN (%100 AYNISI) ---
        if kaynak_id == KAYNAK_GRUP_ID:
            if len(mesajlar) == 1:
                msg = mesajlar[0]
                if msg.photo:
                    # Orijinal Yedek
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
                    # Log (Kimlikli) Yedek
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=LOG_KONU, caption=kisi_linki)
                elif msg.video:
                    # Orijinal Yedek
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
                    # Log (Kimlikli) Yedek
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=LOG_KONU, caption=kisi_linki)
                print("✅ Tekli medya (Orijinal + Log) aktarıldı!")
                
            else:
                yedek_medyalari_hazirla = []
                log_medyalari_hazirla = []
                
                for i, msg in enumerate(mesajlar):
                    orijinal_yazi = "yakalandı" if i == 0 else ""
                    log_yazi = kisi_linki if i == 0 else ""
                    
                    if msg.photo:
                        yedek_medyalari_hazirla.append(InputMediaPhoto(media=msg.photo.file_id, caption=orijinal_yazi))
                        log_medyalari_hazirla.append(InputMediaPhoto(media=msg.photo.file_id, caption=log_yazi))
                    elif msg.video:
                        yedek_medyalari_hazirla.append(InputMediaVideo(media=msg.video.file_id, caption=orijinal_yazi))
                        log_medyalari_hazirla.append(InputMediaVideo(media=msg.video.file_id, caption=log_yazi))
                
                # Orijinal Albüm Yedeği
                await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yedek_medyalari_hazirla, reply_to_message_id=YEDEK_KONU)
                # Log Albüm Yedeği
                await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=log_medyalari_hazirla, reply_to_message_id=LOG_KONU)
                print(f"✅ {len(mesajlar)} parçalı albüm (Orijinal + Log) aktarıldı!")

        # --- B. YENİ EKLENEN KISITLAMALI KANALLAR İÇİN (93842) ---
        else:
            kaynak_adi = mesajlar[0].chat.title or "Bilinmeyen Kaynak"
            mesaj_linki = mesajlar[0].link or "Link Yok"
            
            ortak_aciklama_yeni = (
                f"🚨 **YENİ MEDYA İNDİRİLDİ**\n"
                f"👤 **Gönderen:** {kisi_linki}\n"
                f"📍 **Kaynak:** {kaynak_adi}\n"
                f"🔗 **Bağlantı:** [Orijinal Mesaja Git]({mesaj_linki})"
            )

            if len(mesajlar) == 1:
                msg = mesajlar[0]
                if not getattr(msg, "ram_file_bytes", None): return
                indirilen = ram_dosyasini_isimlendir(msg, BytesIO(msg.ram_file_bytes))
                
                if msg.photo: await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni)
                elif msg.video: await client.send_video(chat_id=YEDEK_GRUP_ID, video=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni)
                elif msg.document: await client.send_document(chat_id=YEDEK_GRUP_ID, document=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni)
                elif msg.audio or msg.voice: await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni)
            else:
                yeni_log_medyalari = []
                for i, msg in enumerate(mesajlar):
                    if not getattr(msg, "ram_file_bytes", None): continue
                    indirilen = ram_dosyasini_isimlendir(msg, BytesIO(msg.ram_file_bytes))
                    yazi = ortak_aciklama_yeni if i == 0 else ""
                    
                    if msg.photo: yeni_log_medyalari.append(InputMediaPhoto(media=indirilen, caption=yazi))
                    elif msg.video: yeni_log_medyalari.append(InputMediaVideo(media=indirilen, caption=yazi))
                    elif msg.document: yeni_log_medyalari.append(InputMediaDocument(media=indirilen, caption=yazi))
                    elif msg.audio: yeni_log_medyalari.append(InputMediaAudio(media=indirilen, caption=yazi))
                
                if yeni_log_medyalari:
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yeni_log_medyalari, reply_to_message_id=YENI_LOG_KONU)

    except Exception as e:
        print(f"❌ Aktarım hatası: {e}")


# ==========================================
# DİNLEYİCİ TETİKLEYİCİ
# ==========================================
@app.on_message(filters.chat(TUM_KAYNAKLAR) & (filters.photo | filters.video | filters.document | filters.audio | filters.voice | filters.video_note))
async def medyayi_dinle(client, message):
    if message.web_page: return 

    if message.chat.id == KAYNAK_GRUP_ID:
        # SENİN ESKİ DİNLEME MANTIĞIN (%100 AYNI)
        mesaj_konu_id = getattr(message, "message_thread_id", None)
        cevap_id = getattr(message, "reply_to_message_id", None)
        
        if mesaj_konu_id == KAYNAK_KONU or cevap_id == KAYNAK_KONU:
            message.ram_file_bytes = None
        else:
            return # Yanlış konuysa geç
    else:
        # EKSTRA KANALLAR İÇİN RAM'E İNDİRME
        try:
            indirilen_ram = await client.download_media(message, in_memory=True)
            if downloaded_bytes := indirilen_ram.getvalue():
                message.ram_file_bytes = downloaded_bytes
            else:
                message.ram_file_bytes = None
        except Exception as e:
            message.ram_file_bytes = None

    grup_id = message.media_group_id or f"tekil_{message.id}"
    
    if grup_id not in album_havuzu:
        album_havuzu[grup_id] = []
        asyncio.create_task(albumu_isle_ve_yolla(client, grup_id))
    
    album_havuzu[grup_id].append(message)

print("🚀 Çift yönlü (Yedek ve Log) iletici Userbot başlatıldı. Kısıtlama bypass ve .indir aktif...")
app.run()
