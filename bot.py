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
from pyrogram.enums import ParseMode
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio

logging.getLogger("pyrogram").setLevel(logging.CRITICAL)

# --- RENDER'I UYANIK TUTMAK İÇİN MİNİ WEB SUNUCUSU ---
class SaglikKontrolu(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Userbot Canlı Sohbet Loglama ve Manuel İndirme Modunda Aktif!".encode("utf-8"))
        
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

# 3. YEDEKLEME VE CANLI LOG AKIŞ KONUSU
YENI_LOG_KONU = 93842

KAYNAK_IDLER = []
for key, value in os.environ.items():
    if key.startswith("KAYNAK_ID"):
        try:
            KAYNAK_IDLER.append(int(value.strip()))
        except ValueError:
            pass

app = Client("benim_userbotum", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

album_havuzu = {}

# Sohbet içine anlık log basmayı sağlayan yardımcı asenkron fonksiyon
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
# YENİ ÖZELLİK: MANUEL LİNKTEN İNDİRME KOMUTU
# ==========================================
@app.on_message(filters.command("indir", prefixes=".") & filters.me)
async def manuel_linkten_indir(client, message):
    if len(message.command) < 2:
        await message.edit_text("❌ **Kullanım:** `.indir https://t.me/...`", parse_mode=ParseMode.MARKDOWN)
        return
        
    link = message.command[1]
    
    try:
        durum_mesaji = await message.edit_text("⏳ **Link analiz ediliyor...**", parse_mode=ParseMode.MARKDOWN)
        
        # Linki Parçalayıp Chat ID ve Message ID'yi Bulma
        parts = link.rstrip("/").split("/")
        
        # Eğer linkte "?single" gibi parametreler varsa temizle
        msg_id_str = parts[-1].split("?")[0]
        msg_id = int(msg_id_str)
        
        if "c" in parts:
            # Gizli grup/kanal formatı: https://t.me/c/1234567890/123
            chat_id = int("-100" + parts[-2])
        else:
            # Açık kanal/grup formatı: https://t.me/KanalAdi/123
            chat_id = parts[-2]
            
        # Mesajı Telegramdan Çek
        msg = await client.get_messages(chat_id, msg_id)
        
        if not msg or msg.empty:
            await durum_mesaji.edit_text("❌ **Mesaj bulunamadı!**\n(O gruba/kanala hesabınızın üye olduğundan emin olun.)", parse_mode=ParseMode.MARKDOWN)
            return
            
        if not msg.media:
            await durum_mesaji.edit_text("❌ **Bu linkte indirilecek herhangi bir medya bulunmuyor.**", parse_mode=ParseMode.MARKDOWN)
            return

        # Komutun yazıldığı yerin tespiti
        hedef_chat = message.chat.id
        hedef_konu = getattr(message, 'message_thread_id', None)
        
        await durum_mesaji.edit_text("⏳ **Medya kısıtlamaları aşılarak RAM'e indiriliyor...**", parse_mode=ParseMode.MARKDOWN)
        
        # ALBÜM KONTROLÜ
        if msg.media_group_id:
            album_mesajlari = await client.get_media_group(chat_id, msg_id)
            medya_grubu = []
            
            for m in album_mesajlari:
                ram_dosyasi = await client.download_media(m, in_memory=True)
                ram_dosyasi = ram_dosyasini_isimlendir(m, ram_dosyasi)
                
                if m.photo: medya_grubu.append(InputMediaPhoto(media=ram_dosyasi))
                elif m.video: medya_grubu.append(InputMediaVideo(media=ram_dosyasi))
                elif m.document: medya_grubu.append(InputMediaDocument(media=ram_dosyasi))
                elif m.audio: medya_grubu.append(InputMediaAudio(media=ram_dosyasi))
            
            await client.send_media_group(chat_id=hedef_chat, media=medya_grubu, reply_to_message_id=hedef_konu)
            
        # TEKLİ MEDYA KONTROLÜ
        else:
            ram_dosyasi = await client.download_media(msg, in_memory=True)
            ram_dosyasi = ram_dosyasini_isimlendir(msg, ram_dosyasi)
            
            if msg.photo: await client.send_photo(chat_id=hedef_chat, photo=ram_dosyasi, reply_to_message_id=hedef_konu)
            elif msg.video: await client.send_video(chat_id=hedef_chat, video=ram_dosyasi, reply_to_message_id=hedef_konu)
            elif msg.audio or msg.voice: await client.send_audio(chat_id=hedef_chat, audio=ram_dosyasi, reply_to_message_id=hedef_konu)
            elif msg.document: await client.send_document(chat_id=hedef_chat, document=ram_dosyasi, reply_to_message_id=hedef_konu)
            elif msg.video_note:
                await client.send_video_note(chat_id=hedef_chat, video_note=ram_dosyasi, reply_to_message_id=hedef_konu)
        
        # İşlem bitince komutu siler
        await durum_mesaji.delete()
        
    except Exception as e:
        await message.edit_text(f"❌ **İndirme hatası:** `{e}`", parse_mode=ParseMode.MARKDOWN)

# ==========================================
# OTO-İLET SİSTEMİ (Arka Plan Dinleyicisi)
# ==========================================
async def albumu_isle_ve_yolla(client, grup_id):
    await asyncio.sleep(2.5) 
    mesajlar = album_havuzu.pop(grup_id, None)
    if not mesajlar: return

    ilk_mesaj = mesajlar[0]
    gonderen = ilk_mesaj.from_user
    kaynak_adi = ilk_mesaj.chat.title or "Bilinmeyen Kaynak"
    mesaj_linki = ilk_mesaj.link or "Link Yok"
    
    if gonderen:
        kisi_linki_eski = f"@{gonderen.username}" if gonderen.username else f"[{gonderen.first_name or 'İsimsiz'}](tg://user?id={gonderen.id})"
    else:
        kisi_linki_eski = "Gizli Kullanıcı/Kanal"

    ortak_aciklama_yeni = (
        f"🚨 <b>YENİ MEDYA İNDİRİLDİ</b>\n"
        f"👤 <b>Gönderen:</b> {kisi_linki_eski}\n"
        f"📍 <b>Kaynak:</b> {kaynak_adi}\n"
        f"🔗 <b>Bağlantı:</b> <a href='{mesaj_linki}'>Orijinal Mesaja Git</a>"
    )

    await sohbet_log_gonder(client, f"🔄 İndirme işlemi başladı. Toplam parça: {len(mesajlar)}")

    try:
        # TEKLİ MEDYA
        if len(mesajlar) == 1:
            msg = mesajlar[0]
            
            # ---> ESKİ SİSTEM YEDEKLEMESİ <---
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
                pass

            # ---> YENİ SİSTEM YEDEKLEMESİ (RAM Bypass 93842'ye) <---
            try:
                indirilen_dosya = await client.download_media(msg, in_memory=True)
                
                if not indirilen_dosya:
                    await sohbet_log_gonder(client, "❌ HATA: Medya RAM hafızasına çekilemedi!")
                    return
                    
                indirilen_dosya = ram_dosyasini_isimlendir(msg, indirilen_dosya)
                
                if msg.photo:
                    await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
                elif msg.video:
                    await client.send_video(chat_id=YEDEK_GRUP_ID, video=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
                elif msg.voice or msg.audio:
                    await client.send_audio(chat_id=YEDEK_GRUP_ID, audio=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
                elif msg.video_note:
                    await client.send_video_note(chat_id=YEDEK_GRUP_ID, video_note=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU)
                    await client.send_message(chat_id=YEDEK_GRUP_ID, text=ortak_aciklama_yeni, reply_to_message_id=YENI_LOG_KONU, parse_mode=ParseMode.HTML)
                elif msg.document:
                    await client.send_document(chat_id=YEDEK_GRUP_ID, document=indirilen_dosya, reply_to_message_id=YENI_LOG_KONU, caption=ortak_aciklama_yeni, parse_mode=ParseMode.HTML)
                
                await sohbet_log_gonder(client, "🎉 İndirilen tekli medya başarıyla 93842 konusuna yüklendi!")
            except Exception as e:
                await sohbet_log_gonder(client, f"❌ İndirilen medyanın yüklenmesinde hata: {e}")

        # ALBÜM İŞLEMLERİ
        else:
            # ---> ESKİ SİSTEM ALBÜM YEDEKLEMESİ <---
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
                
                if eski_yedek_medyalari:
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=eski_yedek_medyalari, reply_to_message_id=YEDEK_KONU)
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=eski_log_medyalari, reply_to_message_id=LOG_KONU)
            except Exception as e:
                pass

            # ---> YENİ SİSTEM ALBÜM YEDEKLEMESİ <---
            try:
                yeni_log_medyalari = []
                for i, msg in enumerate(mesajlar):
                    indirilen_dosya = await client.download_media(msg, in_memory=True)
                    indirilen_dosya = ram_dosyasini_isimlendir(msg, indirilen_dosya)
                    yazi = ortak_aciklama_yeni if i == 0 else ""
                    
                    if msg.photo:
                        yeni_log_medyalari.append(InputMediaPhoto(media=indirilen_dosya, caption=yazi, parse_mode=ParseMode.HTML))
                    elif msg.video:
                        yeni_log_medyalari.append(InputMediaVideo(media=indirilen_dosya, caption=yazi, parse_mode=ParseMode.HTML))
                    elif msg.document:
                        yeni_log_medyalari.append(InputMediaDocument(media=indirilen_dosya, caption=yazi, parse_mode=ParseMode.HTML))
                    elif msg.audio:
                        yeni_log_medyalari.append(InputMediaAudio(media=indirilen_dosya, caption=yazi, parse_mode=ParseMode.HTML))
                
                if yeni_log_medyalari:
                    await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yeni_log_medyalari, reply_to_message_id=YENI_LOG_KONU)
                    await sohbet_log_gonder(client, "🎉 İndirilen albüm grubu başarıyla 93842 konusuna yüklendi!")
            except Exception as e:
                await sohbet_log_gonder(client, f"❌ İndirilen albüm yüklenirken hata: <code>{e}</code>")

    except Exception as e:
        await sohbet_log_gonder(client, f"❌ Kritik Genel İşlem Hatası: <code>{e}</code>")

# Kısıtlama dinlemesi: Belirlenen kaynaklardaki medyaları yakalar
@app.on_message(filters.chat(KAYNAK_IDLER) & (filters.photo | filters.video | filters.document | filters.audio | filters.voice | filters.video_note))
async def medyayi_dinle(client, message):
    if message.web_page: return 

    grup_adi = message.chat.title or "Bilinmeyen Sohbet"
    await sohbet_log_gonder(client, f"👀 <b>Medya Yakalandı!</b>\n📍 <b>Kaynak:</b> {grup_adi}\n🗂 İndirme havuzuna ekleniyor...")

    grup_id = message.media_group_id or f"tekil_{message.id}"
    
    if grup_id not in album_havuzu:
        album_havuzu[grup_id] = []
        asyncio.create_task(albumu_isle_ve_yolla(client, grup_id))
    
    album_havuzu[grup_id].append(message)

print("🚀 3'lü Canlı Sohbet Log ve Manuel İndirme Destekli Userbot Başlatıldı...")
app.run()
