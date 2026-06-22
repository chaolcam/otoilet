import os
import asyncio
import logging
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
from pyrogram.types import InputMediaPhoto, InputMediaVideo

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

# YENİ EKLENEN LOG KONUSU ID'Sİ
LOG_KONU = 78582
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

async def albumu_isle_ve_yolla(client, grup_id):
    await asyncio.sleep(2) 
    mesajlar = album_havuzu.pop(grup_id, None)
    if not mesajlar: return

    # Gönderenin Kimliğini Tespit Etme ve Tıklanabilir Link Oluşturma
    gonderen = mesajlar[0].from_user
    if gonderen:
        if gonderen.username:
            # Kullanıcı adı varsa direkt @username yap
            kisi_linki = f"@{gonderen.username}"
        else:
            # Kullanıcı adı yoksa ismine tıklanabilir profil linki (tg://user) göm
            isim = gonderen.first_name or "Bilinmeyen İsim"
            kisi_linki = f"[{isim}](tg://user?id={gonderen.id})"
    else:
        kisi_linki = "Gizli/Bilinmeyen Kullanıcı"

    try:
        # --- 1. TEKLİ MEDYA İŞLEMLERİ ---
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
            
        # --- 2. ALBÜM İŞLEMLERİ ---
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

    except Exception as e:
        print(f"❌ Aktarım hatası: {e}")

@app.on_message(filters.chat(KAYNAK_GRUP_ID) & (filters.photo | filters.video))
async def medyayi_dinle(client, message):
    mesaj_konu_id = getattr(message, "message_thread_id", None)
    cevap_id = getattr(message, "reply_to_message_id", None)
    
    if mesaj_konu_id == KAYNAK_KONU or cevap_id == KAYNAK_KONU:
        grup_id = message.media_group_id or f"tekil_{message.id}"
        
        if grup_id not in album_havuzu:
            album_havuzu[grup_id] = []
            asyncio.create_task(albumu_isle_ve_yolla(client, grup_id))
        
        album_havuzu[grup_id].append(message)

print("🚀 Çift yönlü (Yedek ve Log) iletici Userbot başlatıldı. İzleme aktif...")
app.run()
