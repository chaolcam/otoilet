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
from pyrogram.enums import ParseMode
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio

logging.getLogger("pyrogram").setLevel(logging.CRITICAL)

# --- RENDER'I UYANIK TUTMAK İÇİN MİNİ WEB SUNUCUSU ---
class SaglikKontrolu(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Userbot Optimize Edilmiş 3 Hatli İletim Sistemiyle Aktif!".encode("utf-8"))
        
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

# 1. HAT: ORİJİNAL KAYNAK GRUP VE KONU AYARLARI
KAYNAK_GRUP_ID = int(os.environ.get("KAYNAK_GRUP_ID"))
KAYNAK_KONU = int(os.environ.get("KAYNAK_KONU"))

YEDEK_GRUP_ID = int(os.environ.get("YEDEK_GRUP_ID"))
YEDEK_KONU = int(os.environ.get("YEDEK_KONU"))
LOG_KONU = 78582

# 2. HAT: EKSTRA KANALLAR VE 93842 KONUSU
YENI_LOG_KONU = 93842
KAYNAK_IDLER = []
for key, value in os.environ.items():
    if key.startswith("KAYNAK_ID"):
        try:
            KAYNAK_IDLER.append(int(value.strip()))
        except ValueError:
            pass

TUM_KAYNAKLAR = [KAYNAK_GRUP_ID] + KAYNAK_IDLER

app = Client("benim_userbotum", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

album_havuzu = {}

async def sohbet_log_gonder(client, metin):
    try:
        await client.send_message(
            chat_id=YEDEK_GRUP_ID,
            text=f"🤖 <b>[SİSTEM LOGU]:</b>\n{metin}",
            reply_to_message_id=YENI_LOG_KONU,
            parse_mode=ParseMode.HTML
        )
    except:
        pass

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
# 3. HAT: MANUEL VE TOPLU İNDİRME (.indir)
# ==========================================
@app.on_message(filters.command("indir", prefixes=".") & filters.me)
async def manuel_linkten_indir(client, message):
    text_to_search = message.text or ""
    if message.reply_to_message:
        text_to_search += " " + (message.reply_to_message.text or message.reply_to_message.caption or "")
        
    links = re.findall(r'https://t\.me/(?:c/)?[a-zA-Z0-9_/-]+', text_to_search)
    links = list(dict.fromkeys([link.split("?")[0].rstrip("/") for link in links]))
    
    if not links:
        await message.edit_text("❌ **Kullanım:** `.indir https://t.me/...`", parse_mode=ParseMode.MARKDOWN)
        return

    durum_mesaji = await message.edit_text(f"⏳ **Toplu indirme başlatılıyor... Toplam: {len(links)}**", parse_mode=ParseMode.MARKDOWN)
    
    hedef_chat = message.chat.id
    hedef_konu = getattr(message, 'message_thread_id', None)
    
    basarili = 0
    hatali = 0
    
    for i, link in enumerate(links, 1):
        try:
            await durum_mesaji.edit_text(f"⏳ **İndiriliyor ({i}/{len(links)})...**", parse_mode=ParseMode.MARKDOWN)
            parts = link.split("/")
            msg_id = int(parts[-1])
            chat_id = int("-100" + parts[-2]) if "c" in parts else parts[-2]
                
            try:
                msg = await client.get_messages(chat_id, msg_id)
            except Exception as e:
                if "Peer id invalid" in str(e).capitalize() or "PEER_ID_INVALID" in str(e):
                    await durum_mesaji.edit_text(f"⏳ **Gizli kanal aranıyor ({i}/{len(links)})...**", parse_mode=ParseMode.MARKDOWN)
                    async for _ in client.get_dialogs(limit=300): pass
                    msg = await client.get_messages(chat_id, msg_id)
                else: raise e
            
            if not msg or msg.empty or not getattr(msg, "media", None):
                hatali += 1
                continue

            if getattr(msg, "media_group_id", None):
                album_mesajlari = await client.get_media_group(chat_id, msg_id)
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
            
    await durum_mesaji.edit_text(f"✅ **İşlem Tamamlandı!**\n📥 İndirilen: `{basarili}` | ❌ Hatalı: `{hatali}`", parse_mode=ParseMode.MARKDOWN)


# ==========================================
# 1. VE 2. HAT: OTO-İLET SİSTEMİ 
# ==========================================
async def albumu_isle_ve_yolla(client, grup_id):
    await asyncio.sleep(2.5) 
    mesajlar = album_havuzu.pop(grup_id, None)
    if not mesajlar: return

    ilk_mesaj = mesajlar[0]
    gonderen = ilk_mesaj.from_user
    kaynak_id = ilk_mesaj.chat.id
    
    if gonderen:
        isim = gonderen.first_name or "İsimsiz Kullanıcı"
        kisi_linki_html = f'<a href="tg://user?id={gonderen.id}">{isim}</a>'
    else:
        kisi_linki_html = "<i>Gizli/Bilinmeyen Kullanıcı</i>"

    # ---> 1. HAT: ORİJİNAL GRUP AYARLARI (YEDEK_KONU ve 78582) <---
    # DİKKAT: Burada RAM'e indirme yok, doğrudan file_id ile ışık hızında yönlendirilir!
    if kaynak_id == KAYNAK_GRUP_ID:
        eski_log_yazisi = f"👤 Gönderen: {kisi_linki_html}"
        
        try:
            if len(mesajlar) == 1:
                msg = mesajlar[0]
                if msg.photo:
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı", parse_mode=ParseMode.HTML)
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=LOG_KONU, caption=eski_log_yazisi, parse_mode=ParseMode.HTML)
                elif msg.video:
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı", parse_mode=ParseMode.HTML)
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=LOG_KONU, caption=eski_log_yazisi, parse_mode=ParseMode.HTML)
                elif msg.document:
                    await client.send_document(chat_id=YEDEK_GRUP_ID, document=msg.document.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı", parse_mode=ParseMode.HTML)
                    await client.send_document(chat_id=YEDEK_GRUP_ID, document=msg.document.file_id, reply_to_message_id=LOG_KONU, caption=eski_log_yazisi, parse_mode=ParseMode.HTML)
                elif msg.audio or msg.voice:
                    await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=(msg.audio.file_id if msg.audio else msg.voice.file_id), reply_to_message_id=YEDEK_KONU, caption="yakalandı", parse_mode=ParseMode.HTML)
                    await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=(msg.audio.file_id if msg.audio else msg.voice.file_id), reply_to_message_id=LOG_KONU, caption=eski_log_yazisi, parse_mode=ParseMode.HTML)
            else:
                yedek_medyalari = []
                log_medyalari = []
                for i, msg in enumerate(mesajlar):
                    o_yazi = "yakalandı" if i == 0 else ""
                    l_yazi = eski_log_yazisi if i == 0 else ""
                    
                    if msg.photo:
                        yedek_medyalari.append(InputMediaPhoto(media=msg.photo.file_id, caption=o_yazi, parse_mode=ParseMode.HTML))
                        log_medyalari.append(InputMediaPhoto(media=msg.photo.file_id, caption=l_yazi, parse_mode=ParseMode.HTML))
                    elif msg.video:
                        yedek_medyalari.append(InputMediaVideo(media=msg.video.file_id, caption=o_yazi, parse_mode=ParseMode.HTML))
                        log_medyalari.append(InputMediaVideo(media=msg.video.file_id, caption=l_yazi, parse_mode=ParseMode.HTML))
                
                if yedek_medyalari:
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yedek_medyalari, reply_to_message_id=YEDEK_KONU)
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=log_medyalari, reply_to_message_id=LOG_KONU)
        except Exception as e:
            print(f"1. Hat Hatası: {e}")

    # ---> 2. HAT: EKSTRA KANALLAR/GRUPLAR (SADECE 93842) <---
    # DİKKAT: Burada medyalar tetikleyici kısmında RAM'e alınmış halden çekilir!
    else:
        kaynak_adi = ilk_mesaj.chat.title or "Bilinmeyen Kaynak"
        mesaj_linki = ilk_mesaj.link or "Link Yok"
        
        ortak_aciklama_yeni = (
            f"🚨 <b>YENİ MEDYA İNDİRİLDİ</b>\n"
            f"👤 <b>Gönderen:</b> {kisi_linki_html}\n"
            f"📍 <b>Kaynak:</b> {kaynak_adi}\n"
            f"🔗 <b>Bağlantı:</b> <a href='{mesaj_linki}'>Orijinal Mesaja Git</a>"
        )
        await sohbet_log_gonder(client, f"🔄 Otomatik kanal indirmesi tamamlandı. Konuya aktarılıyor...")

        try:
            if len(mesajlar) == 1:
                msg = mesajlar[0]
                if not getattr(msg, "ram_file_bytes", None): return
                indirilen = ram_dosyasini_isimlendir(msg, BytesIO(msg.ram_file_bytes))
                
                if msg.photo: await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
                elif msg.video: await client.send_video(chat_id=YEDEK_GRUP_ID, video=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
                elif msg.voice or msg.audio: await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
                elif msg.document: await client.send_document(chat_id=YEDEK_GRUP_ID, document=indirilen, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
            else:
                yeni_log_medyalari = []
                for i, msg in enumerate(mesajlar):
                    if not getattr(msg, "ram_file_bytes", None): continue
                    indirilen = ram_dosyasini_isimlendir(msg, BytesIO(msg.ram_file_bytes))
                    yazi = ortak_aciklama_yeni if i == 0 else ""
                    
                    if msg.photo: yeni_log_medyalari.append(InputMediaPhoto(media=indirilen, caption=yazi, parse_mode=ParseMode.HTML))
                    elif msg.video: yeni_log_medyalari.append(InputMediaVideo(media=indirilen, caption=yazi, parse_mode=ParseMode.HTML))
                    elif msg.document: yeni_log_medyalari.append(InputMediaDocument(media=indirilen, caption=yazi, parse_mode=ParseMode.HTML))
                    elif msg.audio: yeni_log_medyalari.append(InputMediaAudio(media=indirilen, caption=yazi, parse_mode=ParseMode.HTML))
                
                if yeni_log_medyalari:
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yeni_log_medyalari, reply_to_message_id=YENI_LOG_KONU)
        except Exception as e:
            print(f"2. Hat Hatası: {e}")


# ==========================================
# DİNLEYİCİ TETİKLEYİCİ
# ==========================================
@app.on_message(filters.chat(TUM_KAYNAKLAR) & (filters.photo | filters.video | filters.document | filters.audio | filters.voice | filters.video_note))
async def medyayi_dinle(client, message):
    if message.web_page: return 

    if message.chat.id == KAYNAK_GRUP_ID:
        # ANA GRUP İÇİN: Konu kontrolü yap ve RAM indirmesini pas geç (Optimize)
        mesaj_konu_id = getattr(message, "message_thread_id", None)
        cevap_id = getattr(message, "reply_to_message_id", None)
        if mesaj_konu_id != KAYNAK_KONU and cevap_id != KAYNAK_KONU:
            return 
        message.ram_file_bytes = None
    else:
        # EKSTRA KANALLAR İÇİN: Silinmeden ÖNCE tam şu saniyede RAM'e indir!
        try:
            indirilen_ram = await client.download_media(message, in_memory=True)
            if downloaded_bytes := indirilen_ram.getvalue():
                message.ram_file_bytes = downloaded_bytes
            else:
                message.ram_file_bytes = None
        except Exception as e:
            print(f"Anlık indirme başarısız: {e}")
            message.ram_file_bytes = None

    grup_id = message.media_group_id or f"tekil_{message.id}"
    
    if grup_id not in album_havuzu:
        album_havuzu[grup_id] = []
        asyncio.create_task(albumu_isle_ve_yolla(client, grup_id))
    
    album_havuzu[grup_id].append(message)

print("🚀 Userbot Tüm Hatlarıyla ve Hafıza Optimizasyonuyla Başlatıldı!")
app.run()
