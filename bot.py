import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo

logging.getLogger("pyrogram").setLevel(logging.CRITICAL)

# --- AYARLAR ---
API_ID = 3256561 # Kendi API ID'ni yaz (Tırnaksız)
API_HASH = "058a5a139c13d575c3e3ebd19fdefb0a" # Kendi API Hash'ini yaz (Tırnak içinde)
STRING_SESSION = "BAAxsPEAmpe-DfdUfOQ18lI087jVnpPhy3sa5JF1RFOKvbHPbrH3ggN52qMH1DDkz3NhxtbVVkUfT9I_B-LBBA0Nttrt8WPBYLooC78xDTPdCYn_DoVh_6XYvczgyY26L_WWYQ3qCp5BDJrxRWTP7H9KFTp5HvdSYHxe0CiBOSSERX7jpTxAP6DHpKATxI2HqBpskjRMuSp746VYIigadHZ-O6cmG4onRwSRiNu0UyeJCpTQPWkuzNzGX8gpaTR0XTx8J618oIQYxhFHUx5mo9EWPGHq9CtGMFUfB4tU-MAscNC12lkN9uvLLpY2_Wv4Cyzvx6aiEKVVb-d3AKhV9t4Hr-5TwAAAAAGlvNErAA" # Aldığın o çok uzun metni buraya yapıştır (Tırnak içinde)

# 1. ALINACAK YER (Kaynak Grup ve Konu)
KAYNAK_GRUP_ID = -1004357691251
KAYNAK_KONU = 3

# 2. KAYDEDİLECEK YER (Senin Kendi Grubun / Yedek)
YEDEK_GRUP_ID = -1002081318628
YEDEK_KONU = 5695
# ---------------

def susturucu(loop, context):
    hata_metni = str(context.get("exception", ""))
    if "Peer id invalid" in hata_metni or "ID not found" in hata_metni:
        pass 
    else:
        loop.default_exception_handler(context)

loop = asyncio.get_event_loop()
loop.set_exception_handler(susturucu)

app = Client("benim_userbotum", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

album_havuzu = {}

async def albumu_isle_ve_yolla(client, grup_id):
    # Parçaların bota tam ulaşması için 2 saniye bekle
    await asyncio.sleep(2) 
    
    mesajlar = album_havuzu.pop(grup_id, None)
    if not mesajlar: return

    try:
        # EĞER TEK BİR RESİM/VİDEO İSE
        if len(mesajlar) == 1:
            msg = mesajlar[0]
            if msg.photo:
                await client.send_photo(chat_id=YEDEK_GRUP_ID, photo=msg.photo.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
            elif msg.video:
                await client.send_video(chat_id=YEDEK_GRUP_ID, video=msg.video.file_id, reply_to_message_id=YEDEK_KONU, caption="yakalandı")
            print("✅ Başarılı: Tekli medya yakalandı ve kendi grubuna aktarıldı!")
            
        # EĞER ÇOKLU RESİM/VİDEO (ALBÜM) İSE
        else:
            yedek_medyalari_hazirla = []
            for i, msg in enumerate(mesajlar):
                
                # TELEGRAM KURALI: Sadece albümün ilk medyasına caption ekle
                eklenecek_yazi = "yakalandı" if i == 0 else ""
                
                if msg.photo:
                    yedek_medyalari_hazirla.append(InputMediaPhoto(media=msg.photo.file_id, caption=eklenecek_yazi))
                elif msg.video:
                    yedek_medyalari_hazirla.append(InputMediaVideo(media=msg.video.file_id, caption=eklenecek_yazi))
            
            await client.send_media_group(chat_id=YEDEK_GRUP_ID, media=yedek_medyalari_hazirla, reply_to_message_id=YEDEK_KONU)
            print(f"✅ Başarılı: {len(mesajlar)} parçalı albüm yakalandı ve tek parça halinde kendi grubuna aktarıldı!")

    except Exception as e:
        print(f"❌ Aktarım sırasında bir sorun oldu: {e}")

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

print("🚀 Test Modu (Caption Düzeltmesi): Albüm toplama aktif, medyalar SADECE KENDİ GRUBUNA aktarılacak...")
app.run()