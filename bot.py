import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- PYTHON 3.14+ (EVENT LOOP) UYUMLULUK YAMASI ---
# Pyrogram kütüphanesini çağırmadan ÖNCE bir döngü oluşturuyoruz
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
    # Normal tıklatmalar için
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Bot aktif ve çalışıyor!".encode("utf-8"))
        
    # UptimeRobot'un ücretsiz paketindeki tıklatmalar için (YENİ EKLENEN KISIM)
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        
    def log_message(self, format, *args):
        return # Terminal loglarının kirlenmesini önler

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

    try:
        if len(mesajlar) == 1:
            msg = mesajlar[0]
            if msg.photo:
                await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
            elif msg.video:
                await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
            print("✅ Tekli medya kendi grubuna aktarıldı!")
            
        else:
            yedek_medyalari_hazirla = []
            for i, msg in enumerate(mesajlar):
                eklenecek_yazi = "yakalandı" if i == 0 else ""
                if msg.photo:
                    yedek_medyalari_hazirla.append(InputMediaPhoto(media=msg.photo.file_id, caption=eklenecek_yazi))
                elif msg.video:
                    yedek_medyalari_hazirla.append(InputMediaVideo(media=msg.video.file_id, caption=eklenecek_yazi))
            
            await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yedek_medyalari_hazirla, reply_to_message_id=YEDEK_KONU)
            print(f"✅ {len(mesajlar)} parçalı albüm kendi grubuna aktarıldı!")

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

print("🚀 Bulut sunucu üzerinde bot başlatıldı. İzleme aktif...")
app.run()
