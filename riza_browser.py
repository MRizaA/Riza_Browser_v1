#Riza Browser
#By Muhammad Riza Aditya
from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import random
import re
import time
from urllib.parse import urlparse
from datetime import datetime, timedelta

#Backend

class RizaBrowserBackend:
    def __init__(self):
        # Tidak perlu API keys lagi
        self.cache = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def set_api_keys(self, serpapi_key=None, google_cse_id=None, google_api_key=None):
        """
        Method ini dipertahankan untuk kompatibilitas dengan kode lama
        tapi tidak diperlukan lagi untuk fungsi pencarian
        """
        pass  # Tidak melakukan apa-apa

    def search_web(self, query, num_results=5):
        """
        Perform web search using free methods
        """
        # Check cache first
        cache_key = f"web_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try multiple methods until we get results
        results = self._search_with_duckduckgo(query, num_results)

        if not results:
            results = self._search_with_bing(query, num_results)

        if not results:
            # Final fallback if all methods fail
            results = self._generate_fallback_results(query, num_results)

        # Save to cache
        self.cache[cache_key] = results
        return results

    def search_images(self, query, num_results=9):
        """Search for images"""
        cache_key = f"images_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        results = self._search_images_with_bing(query, num_results)

        if not results:
            results = self._generate_image_placeholders(query, num_results)

        self.cache[cache_key] = results
        return results

    def search_videos(self, query, num_results=5):
        """Search for videos"""
        cache_key = f"videos_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        results = self._search_videos_with_bing(query, num_results)

        if not results:
            results = self._generate_video_placeholders(query, num_results)

        self.cache[cache_key] = results
        return results

    # --- Free API Implementations ---

    def _search_with_duckduckgo(self, query, num_results):
        """
        Search using DuckDuckGo (no API key required)
        """
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            for result in soup.select('.result'):
                title_elem = result.select_one('.result__title a')
                snippet_elem = result.select_one('.result__snippet')

                if title_elem and len(results) < num_results:
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')

                    # Extract actual URL from DuckDuckGo redirect
                    if link.startswith('/'):
                        params = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                        if 'uddg' in params:
                            link = params['uddg'][0]

                    snippet = snippet_elem.text.strip() if snippet_elem else ''

                    results.append({
                        'title': title,
                        'url': link,
                        'snippet': snippet
                    })

            return results
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []

    def _search_with_bing(self, query, num_results):
        """
        Search using Bing (no API key required)
        """
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.bing.com/search?q={encoded_query}&setlang=id"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            for result in soup.select('.b_algo'):
                title_elem = result.select_one('h2 a')
                snippet_elem = result.select_one('.b_caption p')

                if title_elem and len(results) < num_results:
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.text.strip() if snippet_elem else ''

                    results.append({
                        'title': title,
                        'url': link,
                        'snippet': snippet
                    })

            return results
        except Exception as e:
            print(f"Bing search error: {e}")
            return []

    def _search_images_with_bing(self, query, num_results):
        """
        Search images using Bing Images (no API key required)
        """
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.bing.com/images/search?q={encoded_query}&qft=+filterui:photo-photo&FORM=RESTAB"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # Extract image data from JavaScript
            image_data_regex = r'var IG=({.+?});'
            match = re.search(image_data_regex, response.text)

            results = []

            if match:
                try:
                    # Try to extract JSON data
                    json_str = match.group(1)
                    # Clean up the JSON string
                    json_str = re.sub(r'([{,])([a-zA-Z0-9_]+):', r'\1"\2":', json_str)
                    data = json.loads(json_str)

                    # Parse image data
                    if 'images' in data and isinstance(data['images'], list):
                        for img in data['images'][:num_results]:
                            if isinstance(img, dict) and 'murl' in img:
                                thumb = img.get('turl', '')
                                full_url = img.get('murl', '')
                                title = img.get('t', '')
                                source = urlparse(img.get('purl', '')).netloc

                                results.append({
                                    'url': full_url,
                                    'thumbnail': thumb,
                                    'title': title,
                                    'source': source
                                })
                except Exception as json_error:
                    print(f"JSON parsing error: {json_error}")

            # If JSON extraction failed, try HTML parsing
            if not results:
                soup = BeautifulSoup(response.text, 'html.parser')

                for img in soup.select('.imgpt a.iusc')[:num_results]:
                    try:
                        m = img.get('m', '')
                        if m:
                            # Clean up the JSON string
                            m = m.replace('\\', '\\\\').replace("'", "\\'")
                            m_data = json.loads(m)

                            title = m_data.get('t', '')
                            full_url = m_data.get('murl', '')
                            thumb = m_data.get('turl', '')
                            source = urlparse(m_data.get('purl', '')).netloc

                            results.append({
                                'url': full_url,
                                'thumbnail': thumb,
                                'title': title,
                                'source': source
                            })
                    except Exception as e:
                        continue

            return results
        except Exception as e:
            print(f"Bing image search error: {e}")
            return []

    def _search_videos_with_bing(self, query, num_results):
        """
        Search videos using Bing Videos (no API key required)
        """
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.bing.com/videos/search?q={encoded_query}&FORM=HDRSC3"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # Find video data in script tags
            script_tags = soup.find_all('script')
            video_data = None

            for script in script_tags:
                if script.string and 'searchResults' in script.string:
                    try:
                        # Extract JSON data
                        match = re.search(r'searchResults\s*:\s*(\[.+?\])', script.string)
                        if match:
                            videos_json = match.group(1)
                            # Fix JSON format for parsing
                            videos_json = re.sub(r'([{,])([a-zA-Z0-9_]+):', r'\1"\2":', videos_json)
                            video_data = json.loads(videos_json)
                            break
                    except Exception:
                        continue

            # Parse video data from JSON
            if video_data and isinstance(video_data, list):
                for video in video_data[:num_results]:
                    if isinstance(video, dict):
                        title = video.get('tt', '')
                        url = video.get('mediaurl', '')
                        thumbnail = video.get('thumb', '')
                        duration = video.get('du', '')

                        # Extract publisher/channel
                        publisher = video.get('pubname', '')

                        # Get views (may not be available)
                        views = video.get('views', '')
                        if views:
                            views = f"{views} views"

                        # Estimated date
                        date = video.get('md', '')
                        if not date:
                            days = random.randint(1, 30)
                            date = f"{days} hari yang lalu"

                        results.append({
                            'title': title,
                            'url': url,
                            'duration': duration,
                            'channel': publisher,
                            'views': views,
                            'date': date,
                            'thumbnail': thumbnail
                        })

            # If JSON extraction failed, fall back to HTML parsing
            if not results:
                for video_item in soup.select('.dg_u')[:num_results]:
                    try:
                        # Get metadata
                        meta_elem = video_item.select_one('.mc_vtvc_meta')
                        title_elem = video_item.select_one('.mc_vtvc_title')
                        thumb_elem = video_item.select_one('.rms_iac')
                        link_elem = video_item.select_one('a')

                        if title_elem and link_elem:
                            title = title_elem.text.strip()
                            url = link_elem.get('href', '')
                            if not url.startswith('http'):
                                url = f"https://www.bing.com{url}"

                            # Duration
                            duration_elem = video_item.select_one('.mc_vtvc_duration')
                            duration = duration_elem.text.strip() if duration_elem else ""

                            # Thumbnail
                            thumbnail = ""
                            if thumb_elem:
                                data_src = thumb_elem.get('data-src', '')
                                src = thumb_elem.get('src', '')
                                thumbnail = data_src or src

                            # Channel name
                            publisher_elem = video_item.select_one('.mc_vtvc_meta_row_publisher')
                            channel = publisher_elem.text.strip() if publisher_elem else "Unknown"

                            # Views and date (these may not be available)
                            views = ""
                            date = ""

                            meta_rows = meta_elem.select('.mc_vtvc_meta_row') if meta_elem else []
                            if len(meta_rows) > 1:
                                meta_text = meta_rows[1].text.strip()
                                # Try to extract views and date
                                if 'views' in meta_text.lower():
                                    views = meta_text
                                else:
                                    date = meta_text

                            if not date:
                                days = random.randint(1, 30)
                                date = f"{days} hari yang lalu"

                            results.append({
                                'title': title,
                                'url': url,
                                'duration': duration,
                                'channel': channel,
                                'views': views,
                                'date': date,
                                'thumbnail': thumbnail
                            })
                    except Exception as parsing_error:
                        continue

            return results
        except Exception as e:
            print(f"Bing video search error: {e}")
            return []

    # --- Fallback Generators ---

    def _generate_fallback_results(self, query, num_results):
        """Generate fallback results when no search method works"""
        results = []
        for i in range(num_results):
            results.append({
                'title': f"{query} - Hasil {i+1} (Mode Offline)",
                'url': f"https://example.com/search?q={urllib.parse.quote(query)}&result={i+1}",
                'snippet': f"Ini adalah hasil contoh untuk pencarian '{query}'. Server pencarian mungkin sedang tidak tersedia."
            })
        return results

    def _generate_image_placeholders(self, query, num_results):
        """Generate placeholder image results"""
        colors = ["ff5733", "33ff57", "3357ff", "f3ff33", "ff33f3", "33fff3"]
        results = []

        for i in range(num_results):
            color = colors[i % len(colors)]
            width = 200
            height = 200
            results.append({
                'url': f"https://via.placeholder.com/{width}x{height}/{color}/000000?text={urllib.parse.quote(query)}",
                'thumbnail': f"https://via.placeholder.com/150x150/{color}/000000?text={urllib.parse.quote(query)}",
                'title': f"{query} gambar {i+1}",
                'source': "placeholder.com"
            })

        return results

    def _generate_video_placeholders(self, query, num_results):
        """Generate placeholder video results"""
        durations = ["5:27", "10:03", "3:15", "8:42", "12:59"]
        channels = ["TechChannel", "RizaVids", "LearnWithMe", "ExpertTips", "TutorialHub"]

        results = []
        for i in range(num_results):
            duration = durations[i % len(durations)]
            channel = channels[i % len(channels)]
            views = f"{random.randint(10, 999)}K"
            days = random.randint(1, 30)

            results.append({
                'title': f"{query} - Part {i+1}",
                'url': f"https://example.com/video/{urllib.parse.quote(query)}/{i+1}",
                'duration': duration,
                'channel': channel,
                'views': views,
                'date': f"{days} hari yang lalu",
                'thumbnail': f"https://via.placeholder.com/300x200/333333/ffffff?text={urllib.parse.quote(query)}+Video"
            })

        return results



backend = RizaBrowserBackend()



#Frontend

class RizaBrowser:
    def __init__(self):
        self.setup_styling()
        self.create_components()
        self.setup_layout()
        self.attach_handlers()

    def setup_styling(self):
        # Apply some custom styling to improve the UI appearance
        display(HTML("""
        <style>
        .widget-button {
            border-radius: 4px;
            transition: all 0.2s;
        }
        .widget-button:hover {
            background-color: #e0e0e0;
        }
        .active-tab {
            background-color: #4285f4 !important;
            color: white !important;
        }
        .search-results {
            font-family: Arial, sans-serif;
        }
        .result-title {
            color: #1a0dab;
            font-size: 18px;
            margin-bottom: 4px;
            cursor: pointer;
        }
        .result-url {
            color: #006621;
            font-size: 14px;
            margin-bottom: 4px;
        }
        .result-snippet {
            color: #545454;
            font-size: 14px;
            margin-bottom: 18px;
        }
        .logo {
            font-family: 'Arial', sans-serif;
            font-size: 24px;
            font-weight: bold;
            color: #4285f4;
            margin-bottom: 10px;
        }
        </style>
        """))

    def create_components(self):
        # Logo
        self.logo = widgets.HTML(
            value='<div class="logo">RizaBrowser</div>'
        )

        # Search bar with button
        self.search_bar = widgets.Text(
            value='',
            placeholder='Cari sesuatu di RizaBrowser...',
            layout=widgets.Layout(width='70%')
        )
        self.search_button = widgets.Button(
            description='🔍 Cari',
            button_style='primary',
            layout=widgets.Layout(width='100px')
        )

        # Navigation tabs
        self.tab_web = widgets.Button(description="Web", layout=widgets.Layout(width='100px'))
        self.tab_images = widgets.Button(description="Gambar", layout=widgets.Layout(width='100px'))
        self.tab_videos = widgets.Button(description="Video", layout=widgets.Layout(width='100px'))
        self.tab_buttons = widgets.HBox([self.tab_web, self.tab_images, self.tab_videos])

        # Active tab tracker
        self.active_tab = "Web"
        self.tab_web.add_class("active-tab")

        # Sidebar toggle and content
        self.nav_toggle = widgets.ToggleButton(
            description="☰ Menu",
            layout=widgets.Layout(width='100px')
        )

        # Sidebar items
        self.nav_items = [
            ("🔒 Filter Konten", self.show_filter_menu),
            ("🛡 Ad Block", self.show_adblock_info),
            ("🔐 VPN Global", self.show_vpn_info),
            ("🤖 AI Assistant", self.show_ai_info),
            ("☁️ Cloud Storage", self.show_cloud_info),
            ("⚙️ Pengaturan", self.show_settings)
        ]

        self.nav_buttons = []
        for name, func in self.nav_items:
            btn = widgets.Button(
                description=name,
                layout=widgets.Layout(width='200px', margin='2px')
            )
            btn.on_click(func)
            self.nav_buttons.append(btn)

        self.nav_box = widgets.VBox(self.nav_buttons)
        self.nav_box.layout.display = 'none'

        # Progress bar for loading simulation
        self.progress = widgets.IntProgress(
            value=0,
            min=0,
            max=100,
            description='Loading:',
            style={'bar_color': '#4285f4'},
            layout=widgets.Layout(width='90%', visibility='hidden')
        )

        # Main output area
        self.output_area = widgets.Output()

        # Status bar
        self.status_bar = widgets.HTML(
            value='<div style="color:#6e6e6e; font-size:12px;">Ready</div>'
        )

    def setup_layout(self):
        # Search area
        search_area = widgets.HBox([self.search_bar, self.search_button])

        # Content area
        content_area = widgets.VBox([
            self.logo,
            search_area,
            self.tab_buttons,
            self.progress,
            self.output_area,
            self.status_bar
        ])

        # Main layout
        self.main_layout = widgets.HBox([
            widgets.VBox([self.nav_toggle, self.nav_box]),
            content_area
        ])

    def attach_handlers(self):
        # Search handlers
        self.search_bar.on_submit(self.on_search_submit)
        self.search_button.on_click(lambda b: self.on_search_submit(self.search_bar))

        # Tab handlers
        self.tab_web.on_click(lambda b: self.switch_tab("Web"))
        self.tab_images.on_click(lambda b: self.switch_tab("Gambar"))
        self.tab_videos.on_click(lambda b: self.switch_tab("Video"))

        # Toggle sidebar
        self.nav_toggle.observe(self.toggle_nav, names='value')

    def toggle_nav(self, change):
        self.nav_box.layout.display = 'flex' if change['new'] else 'none'

    def switch_tab(self, tab_name):
        # Remove active class from all tabs
        self.tab_web.remove_class("active-tab")
        self.tab_images.remove_class("active-tab")
        self.tab_videos.remove_class("active-tab")

        # Add active class to selected tab
        if tab_name == "Web":
            self.tab_web.add_class("active-tab")
        elif tab_name == "Gambar":
            self.tab_images.add_class("active-tab")
        elif tab_name == "Video":
            self.tab_videos.add_class("active-tab")

        self.active_tab = tab_name

        # Perform search with new tab if there's a query
        if self.search_bar.value:
            self.on_search_submit(self.search_bar)

    def on_search_submit(self, sender):
        query = sender.value.strip()
        if not query:
            return

        # Show loading animation
        self.progress.layout.visibility = 'visible'
        self.progress.value = 0
        self.status_bar.value = f'<div style="color:#6e6e6e; font-size:12px;">Searching for: {query}</div>'

        # Simulate loading
        for i in range(101):
            self.progress.value = i
            if i % 20 == 0:
                time.sleep(0.05)

        # Display results based on active tab
        with self.output_area:
            clear_output()
            if self.active_tab == "Web":
                self.display_web_results(query)
            elif self.active_tab == "Gambar":
                self.display_image_results(query)
            elif self.active_tab == "Video":
                self.display_video_results(query)

        # Hide progress bar when done
        self.progress.layout.visibility = 'hidden'
        self.status_bar.value = f'<div style="color:#6e6e6e; font-size:12px;">Found results for: {query}</div>'

    def display_web_results(self, query):
        # Ganti dengan pencarian nyata
        results = backend.search_web(query)

        html = '<div class="search-results">'
        for result in results:
            html += f'''
            <div>
                <div class="result-title" onclick="window.open('{result["url"]}', '_blank')">{result["title"]}</div>
                <div class="result-url">{result["url"]}</div>
                <div class="result-snippet">{result["snippet"]}</div>
            </div>
            '''
        html += '</div>'

        display(HTML(html))


    def display_image_results(self, query):
        # Ganti dengan pencarian gambar nyata
        results = backend.search_images(query)

        html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        for i, result in enumerate(results):
            html += f'''
            <div style="margin-bottom: 10px;">
            <img src="{result['thumbnail']}"
                 alt="{result['title']}"
                 style="border-radius: 5px; cursor: pointer; height: 150px; width: 150px; object-fit: cover;"
                 onclick="window.open('{result['url']}', '_blank')" />
            <div style="font-size: 12px; color: #1a0dab; margin-top: 3px; width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {result['title']}
            </div>
            </div>
            '''
        html += '</div>'

        display(HTML(html))

    def display_video_results(self, query):
        # Ganti dengan pencarian video nyata
        results = backend.search_videos(query)

        html = '<div>'
        for result in results:
            html += f'''
            <div style="display: flex; margin-bottom: 20px; cursor: pointer;">
            <div style="margin-right: 15px;">
                <div style="position: relative;">
                    <img src="{result['thumbnail']}" alt="{result['title']}" style="border-radius: 8px; width: 220px; height: 120px; object-fit: cover;"
                         onclick="window.open('{result['url']}', '_blank')" />
                    <div style="position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,0.7); color: white; padding: 2px 4px; border-radius: 2px; font-size: 12px;">
                        {result['duration']}
                    </div>
                </div>
            </div>
            <div>
                <div style="font-weight: bold; font-size: 16px;" onclick="window.open('{result['url']}', '_blank')">
                    {result['title']}
                </div>
                <div style="color: #606060; font-size: 14px; margin-top: 5px;">
                    {result['channel']} • {result['views']} ditonton • {result['date']}
                </div>
                <div style="color: #606060; font-size: 14px; margin-top: 8px;">
                    Video tentang {query}. Klik untuk menonton.
                </div>
            </div>
            </div>
            '''
        html += '</div>'

        display(HTML(html))


    # Sidebar menu functions
    def show_filter_menu(self, _):
        with self.output_area:
            clear_output()
            filter_options = widgets.RadioButtons(
                options=[
                    "Mode Anak",
                    "Moderate",
                    "Uncensored (Premium)",
                    "Custom Filter (Premium)"
                ],
                description="Filter:",
                disabled=False
            )
            display(HTML("<h3>🔒 Pengaturan Filter Konten</h3>"))
            display(filter_options)

            apply_button = widgets.Button(description="Terapkan", button_style="primary")
            display(apply_button)

    def show_adblock_info(self, _):
        with self.output_area:
            clear_output()
            display(HTML("""
            <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px;">
                <h3>🛡 Ad Block Premium</h3>
                <p>Fitur ini akan menghilangkan semua jenis iklan di situs web, termasuk:</p>
                <ul>
                    <li>Pop-up ads</li>
                    <li>Video ads</li>
                    <li>Banner ads</li>
                    <li>Tracking cookies</li>
                </ul>
                <div style="color: #e74c3c; font-style: italic; margin-top: 20px;">
                    <b>Fitur ini belum tersedia (Premium)</b>
                </div>
            </div>
            """))

    def show_vpn_info(self, _):
        with self.output_area:
            clear_output()
            display(HTML("""
            <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px;">
                <h3>🔐 VPN Global</h3>
                <p>Aktifkan VPN untuk mengamankan data Anda saat browsing dan menikmati fitur berikut:</p>
                <ul>
                    <li>Enkripsi data tingkat lanjut</li>
                    <li>Akses konten terblokir di wilayah Anda</li>
                    <li>Melindungi identitas Anda saat online</li>
                    <li>Server di 50+ negara</li>
                </ul>
                <div style="color: #e74c3c; font-style: italic; margin-top: 20px;">
                    <b>Fitur ini belum tersedia (Premium)</b>
                </div>
            </div>
            """))

    def show_ai_info(self, _):
        with self.output_area:
            clear_output()
            display(HTML("""
            <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px;">
                <h3>🤖 AI Assistant</h3>
                <p>Dapatkan jawaban pintar langsung dari tab pencarian Anda:</p>
                <ul>
                    <li>Jawaban instan untuk pertanyaan kompleks</li>
                    <li>Ringkasan otomatis dari halaman web</li>
                    <li>Terjemahan real-time</li>
                    <li>Rekomendasi konten personal</li>
                </ul>
                <div style="color: #e74c3c; font-style: italic; margin-top: 20px;">
                    <b>Fitur ini belum tersedia (Premium)</b>
                </div>
            </div>
            """))

    def show_cloud_info(self, _):
        with self.output_area:
            clear_output()
            display(HTML("""
            <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px;">
                <h3>☁️ Cloud Storage</h3>
                <p>Simpan dan sinkronkan data browsing Anda secara online:</p>
                <ul>
                    <li>Bookmark dan favorit</li>
                    <li>Riwayat pencarian</li>
                    <li>Pengaturan dan preferensi</li>
                    <li>5GB penyimpanan gratis (upgrade tersedia)</li>
                </ul>
                <div style="color: #e74c3c; font-style: italic; margin-top: 20px;">
                    <b>Fitur ini belum tersedia (Premium)</b>
                </div>
            </div>
            """))

    def show_settings(self, _):
        with self.output_area:
            clear_output()
            display(HTML("<h3>⚙️ Pengaturan</h3>"))

            # Setting options
            language_dropdown = widgets.Dropdown(
                options=['Bahasa Indonesia', 'English', 'Español', '日本語', '한국어'],
                value='Bahasa Indonesia',
                description='Bahasa:',
                disabled=False,
            )

            theme_buttons = widgets.RadioButtons(
                options=['Light', 'Dark', 'System Default'],
                value='Light',
                description='Tema:',
                disabled=False
            )

            save_button = widgets.Button(
                description="Simpan Pengaturan",
                button_style="success",
                icon="check"
            )

            display(language_dropdown)
            display(theme_buttons)
            display(save_button)

    def run(self):
        display(self.main_layout)
        with self.output_area:
            display(HTML("""
            <div style="text-align: center; padding: 50px 0;">
                <div style="font-size: 24px; font-weight: bold; color: #4285f4; margin-bottom: 20px;">
                    Selamat Datang di RizaBrowser
                </div>
                <div style="color: #5f6368; font-size: 16px;">
                    Ketik kata kunci di kotak pencarian untuk memulai
                </div>
            </div>
            """))

# Instantiate and run the browser
browser = RizaBrowser()
browser.run()
