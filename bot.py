import os
import asyncio
import logging
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
        self.wfile.write("Userbot aktif, 3'lü yedekleme ve kısıtlı medya bypass sistemi çalışıyor!".encode("utf-8"))
        
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

# 1. VE 2. YEDEKLEME (ESKİ SİSTEM İÇİN)
YEDEK_GRUP_ID = int(os.environ.get("YEDEK_GRUP_ID"))
YEDEK_KONU = int(os.environ.get("YEDEK_KONU"))
LOG_KONU = 78582

# 3. YEDEKLEME (YENİ BYPASSLI, DETAYLI SİSTEM İÇİN)
YENI_LOG_KONU = 93842

# KAYNAK KANALLAR/GRUPLAR (Render ortam değişkenlerinden KAYNAK_ID_ ile başlayanları çeker)
KAYNAK_IDLER = []
for key, value in os.environ.items():
    if key.startswith("KAYNAK_ID"):
        try:
            KAYNAK_IDLER.append(int(value.strip()))
        except ValueError:
            pass

if not KAYNAK_IDLER:
    print("⚠️ UYARI: Render paneline hiç KAYNAK_ID_... değişkeni eklemediniz!")
else:
    print(f"📡 Dinlenen Kaynak Sayısı: {len(KAYNAK_IDLER)}")
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

# Medyanın doğru formatta yüklenmesi için uzantı belirleyici yardımcı fonksiyon
def ram_dosyasini_isimlendir(msg, ram_dosyasi):
    if msg.photo: 
        ram_dosyasi.name = "gorsel.jpg"
    elif msg.video: 
        ram_dosyasi.name = "video.mp4"
    elif msg.voice: 
        ram_dosyasi.name = "ses_kaydi.ogg"
    elif msg.audio: 
        ram_dosyasi.name = getattr(msg.audio, "file_name", "muzik.mp3")
    elif msg.video_note: 
        ram_dosyasi.name = "yuvarlak_video.mp4"
    elif msg.document: 
        ram_dosyasi.name = getattr(msg.document, "file_name", "belge.file")
    else:
        ram_dosyasi.name = "bilinmeyen_dosya.dat"
    return ram_dosyasi

async def albumu_isle_ve_yolla(client, grup_id):
    await asyncio.sleep(2.5) 
    mesajlar = album_havuzu.pop(grup_id, None)
    if not mesajlar: return

    # Gönderen ve Kaynak Bilgileri
    ilk_mesaj = mesajlar[0]
    gonderen = ilk_mesaj.from_user
    kaynak_adi = ilk_mesaj.chat.title or "Bilinmeyen Kaynak"
    mesaj_linki = ilk_mesaj.link or "Link Yok"
    
    # Eski sistem için Markdown linki
    if gonderen:
        kisi_linki_eski = f"@{gonderen.username}" if gonderen.username else f"[{gonderen.first_name or 'İsimsiz'}](tg://user?id={gonderen.id})"
    else:
        kisi_linki_eski = "Gizli Kullanıcı/Kanal"

    # Yeni sistem için HTML detaylı açıklama
    ortak_aciklama_yeni = (
        f"🚨 <b>YENİ MEDYA YAKALANDI</b>\n"
        f"👤 <b>Gönderen:</b> {kisi_linki_eski}\n"
        f"📍 <b>Kaynak:</b> {kaynak_adi}\n"
        f"🔗 <b>Bağlantı:</b> <a href='{mesaj_linki}'>Orijinal Mesaja Git</a>"
    )

    try:
        # ==========================================
        # 1. TEKLİ MEDYA İŞLEMLERİ
        # ==========================================
        if len(mesajlar) == 1:
            msg = mesajlar[0]
            
            # ---> A) ESKİ SİSTEM YEDEKLEMESİ (file_id kullanarak YEDEK_KONU ve 78582'ye) <---
            try:
                if msg.photo:
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=LOG_KONU, caption=kisi_linki_eski)
                elif msg.video:
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=LOG_KONU, caption=kisi_linki_eski)
                elif msg.document:
                    await client.send_document(chat_id=YEDEK_GRUP_ID, document=msg.document.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
                    await client.send_document(chat_id=YEDEK_GRUP_ID, document=msg.document.file_id, reply_to_message_id=LOG_KONU, caption=kisi_linki_eski)
                elif msg.audio or msg.voice:
                    await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=(msg.audio.file_id if msg.audio else msg.voice.file_id), reply_to_message_id=YEDEK_KONU, caption="yakalandı")
                    await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=(msg.audio.file_id if msg.audio else msg.voice.file_id), reply_to_message_id=LOG_KONU, caption=kisi_linki_eski)
            except Exception as e:
                print(f"Eski sistem tekli medya aktarımı başarısız (Grup kopyalamaya kapalı olabilir): {e}")

            # ---> B) YENİ SİSTEM YEDEKLEMESİ (RAM Bypass kullanarak 93842'ye) <---
            try:
                indirilen_dosya = await client.download_media(msg, in_memory=True)
                indirilen_dosya = ram_dosyasini_isimlendir(msg, indirilen_dosya)
                
                if msg.photo:
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode="HTML")
                elif msg.video:
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode="HTML")
                elif msg.voice or msg.audio:
                    await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode="HTML")
                elif msg.video_note:
                    await client.send_video_note(chat_id=YEDEK_GRUP_ID, video_note=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU)
                    await client.send_message(chat_id=YEDEK_GRUP_ID, text=ortak_aciklama_yeni, reply_to_message_id=YENI_LOG_KONU, disable_web_page_preview=True, parse_mode="HTML")
                elif msg.document:
                    await client.send_document(chat_id=YEDEK_GRUP_ID, document=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode="HTML")
            except Exception as e:
                print(f"Yeni sistem tekli RAM aktarımı başarısız: {e}")

            print("✅ Tekli medya (Eski ve Yeni Konular) işlemi tamamlandı.")
            
        # ==========================================
        # 2. ALBÜM İŞLEMLERİ
        # ==========================================
        else:
            # ---> A) ESKİ SİSTEM ALBÜM YEDEKLEMESİ (file_id kullanarak YEDEK_KONU ve 78582'ye) <---
            try:
                eski_yedek_medyalari = []
                eski_log_medyalari = []
                
                for i, msg in enumerate(mesajlar):
                    orijinal_yazi = "yakalandı" if i == 0 else ""
                    log_yazi = kisi_linki_eski if i == 0 else ""
                    
                    if msg.photo:
                        eski_yedek_medyalari.append(InputMediaPhoto(media=msg.photo.file_id, caption=orijinal_yazi))
                        eski_log_medyalari.append(InputMediaPhoto(media=msg.photo.file_id, caption=log_yazi))
                    elif msg.video:
                        eski_yedek_medyalari.append(InputMediaVideo(media=msg.video.file_id, caption=orijinal_yazi))
                        eski_log_medyalari.append(InputMediaVideo(media=msg.video.file_id, caption=log_yazi))
                    elif msg.document:
                        eski_yedek_medyalari.append(InputMediaDocument(media=msg.document.file_id, caption=orijinal_yazi))
                        eski_log_medyalari.append(InputMediaDocument(media=msg.document.file_id, caption=log_yazi))
                
                if eski_yedek_medyalari:
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=eski_yedek_medyalari, reply_to_message_id=YEDEK_KONU)
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=eski_log_medyalari, reply_to_message_id=LOG_KONU)
            except Exception as e:
                print(f"Eski sistem albüm aktarımı başarısız: {e}")

            # ---> B) YENİ SİSTEM ALBÜM YEDEKLEMESİ (RAM Bypass kullanarak 93842'ye) <---
            try:
                yeni_log_medyalari = []
                
                for i, msg in enumerate(mesajlar):
                    indirilen_dosya = await client.download_media(msg, in_memory=True)
                    indirilen_dosya = ram_dosyasini_isimlendir(msg, indirilen_dosya)
                    yazi = ortak_aciklama_yeni if i == 0 else ""
                    
                    if msg.photo:
                        yeni_log_medyalari.append(InputMediaPhoto(media=indirilen_dosya, caption=yazi, parse_mode="HTML"))
                    elif msg.video:
                        yeni_log_medyalari.append(InputMediaVideo(media=indirilen_dosya, caption=yazi, parse_mode="HTML"))
                    elif msg.document:
                        yeni_log_medyalari.append(InputMediaDocument(media=indirilen_dosya, caption=yazi, parse_mode="HTML"))
                    elif msg.audio:
                        yeni_log_medyalari.append(InputMediaAudio(media=indirilen_dosya, caption=yazi, parse_mode="HTML"))
                
                if yeni_log_medyalari:
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yeni_log_medyalari, reply_to_message_id=YENI_LOG_KONU)
            except Exception as e:
                print(f"Yeni sistem RAM albüm aktarımı başarısız: {e}")

            print(f"✅ {len(mesajlar)} parçalı albüm (Eski ve Yeni Konular) işlemi tamamlandı.")

    except Exception as e:
        print(f"❌ Beklenmeyen genel aktarım hatası: {e}")

# Kısıtlama dinlemesi: Belirlenen tüm kaynaklardaki (foto, video, ses, belge vb.) medyaları yakalar
@app.on_message(filters.chat(KAYNAK_IDLER) & (filters.photo | filters.video | filters.document | filters.audio | filters.voice | filters.video_note))
async def medyayi_dinle(client, message):
    # İleri dönük web sayfaları (link özetleri) medya olarak sayılmasın diye ufak bir filtre
    if message.web_page: return 

    # Grup mantığı (Albüm mü tekil dosya mı?)
    grup_id = message.media_group_id or f"tekil_{message.id}"
    
    if grup_id not in album_havuzu:
        album_havuzu[grup_id] = []
        asyncio.create_task(albumu_isle_ve_yolla(client, grup_id))
    
    album_havuzu[grup_id].append(message)

print("🚀 3'lü Yedekleme (Orijinal + Log + Kısıtlama Kırıcı) Userbot başlatıldı. İzleme aktif...")
app.run()
