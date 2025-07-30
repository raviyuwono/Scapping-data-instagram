import time
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from colorthief import ColorThief
import webcolors

# === Fungsi helper (Tidak diubah) ===
def closest_color(requested_color):
    min_colors = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]

def get_color_name(rgb_color):
    try:
        return closest_color(rgb_color)
    except Exception:
        return 'unknown'

# === Setup Chrome ===
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# === Login manual ===
driver.get('https://www.instagram.com/')
print("🔑 Silakan login ke akun Instagram Anda di browser yang muncul. Anda punya waktu 20 detik.")
time.sleep(300)

# === Profil target ===
username_target = 'batikkerisonline'
profile_url = f'https://www.instagram.com/{username_target}/'
driver.get(profile_url)
WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.xc3tme8")))
time.sleep(5)


# === PENGAMBILAN DATA PROFIL LENGKAP ===
print("\n🔍 Mengambil data detail profil...")

# -- REVISI: Username & Nama Pengguna --
username = username_target  # Username sudah diketahui
display_name = 'N/A'
try:
    # Ambil elemen `span` dari child pertama `section.xc3tme8`
    display_name_element = driver.find_element(By.CSS_SELECTOR, "section.xc3tme8 > div:nth-child(1) span")
    display_name = display_name_element.text.strip()
except Exception as e:
    print(f"⚠️ Gagal mengambil Nama Pengguna: {e}")





print(f"✅ Username: {username}")
print(f"✅ Nama Pengguna: {display_name}")


# -- Kategori Toko, Bio, Tautan --
kategori_profil = 'N/A'
bio = 'N/A'
tautan = 'N/A'
try:
    kategori_profil_element = driver.find_element(By.CSS_SELECTOR, "div._ap3a._aaco._aacu._aacy._aad6._aade")
    kategori_profil = kategori_profil_element.text
except: print("⚠️ Kategori toko tidak ditemukan.")
print(f"✅ Kategori Profil: {kategori_profil}")

# try:
#     bio_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Katalog detail produk')]")
#     bio = bio_element.text.replace('\n', ' ') # Ganti baris baru dengan spasi
# except: print("⚠️ Bio tidak ditemukan.")
# print(f"✅ Bio: {bio}")
bio = 'N/A'  # Default

try:
    bio_candidates = driver.find_elements(By.CSS_SELECTOR, "span._ap3a")
    
    for candidate in bio_candidates:
        text = candidate.text.strip()
        # Cek apakah kemungkinan besar itu bio
        if '@' in text or 'WA:' in text or 'Shopee' in text or len(text) > 20:
            bio = text.replace('\n', ' ')
            break

except Exception as e:
    print("⚠️ Bio tidak ditemukan:", str(e))

print(f"✅ Bio: {bio}")


try:
    tautan_element = driver.find_element(By.CSS_SELECTOR, "a[href*='l.instagram.com']")
    tautan = tautan_element.text
except: print("⚠️ Tautan tidak ditemukan.")
print(f"✅ Tautan: {tautan}")

# -- Statistik (Posts, Followers, Following) --
total_posts, total_followers, total_following = 'N/A', 'N/A', 'N/A'
try:
    stats_elements = driver.find_elements(By.CSS_SELECTOR, "ul.x78zum5 > li.xl565be")
    for stat in stats_elements:
        text = stat.text
        if 'posts' in text: total_posts = text.split(' ')[0]
        elif 'followers' in text:
            try: total_followers = stat.find_element(By.CSS_SELECTOR, "span[title]").get_attribute('title').replace(',', '')
            except: total_followers = text.split(' ')[0]
        elif 'following' in text: total_following = text.split(' ')[0]
except Exception as e: print(f"⚠️ Gagal mengambil statistik profil: {e}")
print(f"📊 Statistik Profil - Posts: {total_posts}, Followers: {total_followers}, Following: {total_following}")


# === Scroll dan ambil post secara bertahap ===
print("\n⏳ Mulai scroll dan ambil post...")
scroll_times = 1
post_links = []
last_height = driver.execute_script("return document.body.scrollHeight")
for i in range(scroll_times):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    posts = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"], a[href*="/reel/"]')
    for post in posts:
        href = post.get_attribute('href')
        if href and href not in post_links: post_links.append(href)
    print(f"   Scroll ke-{i+1}: total post sekarang {len(post_links)}")
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        print("   Telah mencapai bagian bawah halaman.")
        break
    last_height = new_height

print(f"\n✅ Total post unik ditemukan: {len(post_links)}")
post_links = post_links[:10] 
print(f"\nℹ️  Akan memproses {len(post_links)} post teratas.")

# === DATA OUTPUT ===
all_data = []

# === Loop setiap post ===
for idx, link in enumerate(post_links):
    print(f"\n--- Memproses Post {idx+1}/{len(post_links)}: {link} ---")
    driver.get(link)
    try: WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    except TimeoutException:
        print("❌ Halaman post tidak termuat, melewati post ini.")
        continue
    time.sleep(5)

    id_post = link.split('/')[-2]
    media_type = 'reel' if '/reel/' in link else 'post'
    
    # === Memuat Komentar (Logika yang Anda inginkan dipertahankan) ===
    print("⏳ Memuat semua komentar...")

    while True:
        try:
            # XPath fleksibel untuk semua bahasa
            xpath = "//button[.//*[contains(@aria-label, 'Load more comments') or contains(@aria-label, 'Muat komentar lainnya')]]"
            
            # Temukan tombol
            load_more = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            # Scroll agar bisa diklik
            driver.execute_script("arguments[0].scrollIntoView();", load_more)
            time.sleep(0.3)

            # Tunggu tombol bisa diklik
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )

            # Klik via JavaScript
            driver.execute_script("arguments[0].click();", load_more)
            print("✅ Tombol komentar diklik.")
            time.sleep(5)
        except Exception as e:
            print(f"⛔ Tidak ada tombol komentar lagi atau error: {e}")
            break


    # === PENGAMBILAN DATA POST ===
    caption, likes, media_url, upload_time = '', '0', '', ''
    try: caption = driver.find_element(By.TAG_NAME, 'h1').text.strip()
    except: pass
    try:
        like_element = driver.find_element(By.CSS_SELECTOR, "a[href*='/liked_by/'] span")
        likes = like_element.text.replace(' likes', '').replace(',', '').strip()
    except: pass
    try:
        video_elements = driver.find_elements(By.TAG_NAME, 'video')
        if video_elements: media_url = video_elements[0].get_attribute('src')
        else: media_url = driver.find_element(By.CSS_SELECTOR, "img.x5yr21d").get_attribute('src')
    except: pass
    try: upload_time = driver.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
    except: pass
    content_category = 'Batikula post'

    # === Mengambil semua komentar langsung dengan Selenium ===
    comments_list = []
    print("🕵️  Mengambil teks dari semua komentar yang terlihat...")
    try:
        comment_elements = driver.find_elements(By.CSS_SELECTOR, "ul._a9ym span._aade")
        for element in comment_elements: comments_list.append(element.text.strip())
    except: print("❌ Gagal mengambil komentar dengan Selenium.")
    final_comments = comments_list[:50]
    comments_count_scraped = len(final_comments)
    print(f"✅ Berhasil mengambil {comments_count_scraped} komentar.")
    
    # --- Analisis warna ---
    dominant_color, color_name = '', ''
    if media_url and media_type == 'post':
        try:
            response = requests.get(media_url, timeout=10)
            img = BytesIO(response.content)
            ct = ColorThief(img)
            dominant_color_rgb = ct.get_color(quality=1)
            dominant_color, color_name = str(dominant_color_rgb), get_color_name(dominant_color_rgb)
        except: dominant_color, color_name = 'error', 'error'

    # --- Menyimpan data ke list utama (dengan data profil baru) ---
    data_profil = [username, display_name, kategori_profil, bio, tautan, total_posts, total_followers, total_following]
    if not final_comments:
        all_data.append(data_profil + [
            id_post, link, caption, likes, 0, media_url, media_type,
            dominant_color, color_name, content_category, upload_time, ''
        ])
    else:
        for comment_text in final_comments:
            all_data.append(data_profil + [
                id_post, link, caption, likes, comments_count_scraped, media_url, media_type,
                dominant_color, color_name, content_category, upload_time, comment_text
            ])
    time.sleep(1)

# === Save ke Excel (dengan kolom baru) ===
df = pd.DataFrame(all_data, columns=[
    'username', 'nama_pengguna', 'kategori_profil', 'bio', 'tautan', 
    'total_posts', 'total_followers', 'total_following',
    'id_post', 'url_post', 'caption', 'likes', 'comments_count',
    'media_url', 'media_type', 'dominant_color', 'color_name',
    'content_category', 'upload_time', 'comment'
])

output_filename = f"hasil_scrape_{username_target}.xlsx",
df.to_excel(output_filename, index=False)
print(f"\n✅ Selesai! Data disimpan ke '{output_filename}'")

driver.quit()