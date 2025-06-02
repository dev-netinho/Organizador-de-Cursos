
import requests
from bs4 import BeautifulSoup
import os
import time
import subprocess
from .utils import sanitize_filename, create_folder_structure 
from urllib.parse import urljoin 

class DownloaderEngine:
    def __init__(self, platform_config, base_output_path, course_url, course_name_for_folder, yt_dlp_path=None):
        self.config = platform_config
        self.base_output_path = base_output_path
        self.main_course_url = course_url 
        self.course_name_for_folder = course_name_for_folder
        self.yt_dlp_path = yt_dlp_path if yt_dlp_path else 'yt-dlp'
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
        })
        self.logged_in = False
        self.current_referer = None


    def _make_request(self, url, method="GET", data=None, extra_headers=None, stream=False, timeout=30, allow_redirects=True):
        request_headers = self.session.headers.copy()
        if self.current_referer: 
            request_headers['Referer'] = self.current_referer
        if extra_headers:
            request_headers.update(extra_headers)
        
        try:
            if method.upper() == "POST":
                response = self.session.post(url, headers=request_headers, data=data, timeout=timeout, stream=stream, allow_redirects=allow_redirects)
            else:
                response = self.session.get(url, headers=request_headers, timeout=timeout, stream=stream, allow_redirects=allow_redirects)

            self.current_referer = response.url 
            return response
        except requests.exceptions.RequestException as e:
            print(f"  Erro na requisição para {url}: {e}")
            return None

    def login(self, username, password):
        cfg_login = self.config
        login_page_url = cfg_login["login_page_url"]
        login_action_url = cfg_login.get("login_form_action_url", login_page_url)
        payload_fields = cfg_login["login_payload_fields"]
        
        payload = {
            payload_fields["username"]: username,
            payload_fields["password"]: password,
        }

        for key, value in payload_fields.items():
            if key not in ["username", "password"]:
                payload[key] = value 

        print(f"Tentando login em {login_action_url} (a partir de {login_page_url})")

        response = self._make_request(login_action_url, method="POST", data=payload, extra_headers={'Referer': login_page_url})

        if not response:
            print("Login falhou: Sem resposta do servidor.")
            return False

        # Verificar sucesso no login
        for indicator in cfg_login.get("login_success_indicators", []):
            if indicator["type"] == "url_contains" and indicator["value"] in response.url:
                self.logged_in = True
                break
            if indicator["type"] == "url_is_not" and indicator["value"] != response.url:
                 # Se a URL mudou E não é mais a de login, considera sucesso parcial (ajustar se necessário)
                if login_page_url not in response.url and login_action_url not in response.url:
                    self.logged_in = True
                    break
            if indicator["type"] == "page_text_contains" and indicator["value"] in response.text:
                self.logged_in = True
                break
            if indicator["type"] == "element_exists": # Requer parsing
                soup_login_resp = BeautifulSoup(response.text, 'html.parser')
                if soup_login_resp.find(indicator["selector"]["tag"], indicator["selector"].get("attrs")):
                    self.logged_in = True
                    break
        
        if self.logged_in:
            print("Login bem-sucedido!")
            self.current_referer = response.url
            return True
        else:
            print("Login falhou. Verifique as credenciais e os indicadores de sucesso/falha na configuração da plataforma.")
            # Tenta verificar indicadores de falha
            for indicator in cfg_login.get("login_failure_indicators", []):
                 if indicator["type"] == "page_text_contains" and indicator["value"] in response.text:
                    print(f"  Indicação de falha no login encontrada: {indicator['value']}")
                    break
            # print(response.text[:1500]) # Para depuração
            return False

    def _find_elements_from_soup(self, soup, selector_config):
        tag = selector_config.get("tag")
        attrs = selector_config.get("attrs", {})
        if not tag: return []
        return soup.find_all(tag, attrs)

    def _get_text_from_element(self, element, selector_config=None, default_text="Desconhecido"):
        if not element: return default_text
        target_element = element
        if selector_config and selector_config.get("tag"): # Se o seletor for para um sub-elemento
            target_element = element.find(selector_config["tag"], selector_config.get("attrs", {}))
        return target_element.get_text(strip=True) if target_element else default_text

    def _get_href_from_element(self, element, selector_config=None, base_url=""):
        if not element: return None
        target_element = element
        if selector_config and selector_config.get("tag"): # Se o seletor for para um sub-elemento
            target_element = element.find(selector_config["tag"], selector_config.get("attrs", {}))
        
        href = target_element.get('href') if target_element else None
        return urljoin(base_url, href) if href else None


    def process_course(self):
        if not self.logged_in:
            print("ERRO: Não logado. Execute o login primeiro.")
            return

        print(f"\nAcessando página do curso: {self.main_course_url}")
        response_course_page = self._make_request(self.main_course_url, extra_headers={'Referer': self.current_referer or self.main_course_url})
        if not response_course_page or response_course_page.status_code != 200:
            print(f"Falha ao acessar a página principal do curso: {self.main_course_url}")
            return

        print("Página do curso acessada. Analisando estrutura...")
        soup_course_page = BeautifulSoup(response_course_page.text, 'html.parser')
        
        cfg_selectors = self.config["selectors"]
        overall_lesson_counter = 0
        
        # --- Encontrar Módulos ---
        module_elements = self._find_elements_from_soup(soup_course_page, cfg_selectors["module_item_selector"])
        print(f"Encontrados {len(module_elements)} módulos.")

        for module_element in module_elements:
            module_title = self._get_text_from_element(module_element, cfg_selectors["module_title_selector_from_item"], "Módulo Desconhecido")
            print(f"\n--- Processando Módulo: {module_title} ---")

            lesson_container_element = module_element # Por padrão, aulas estão dentro do item do módulo
            if cfg_selectors.get("lesson_list_container_from_module"):
                sel_tag = cfg_selectors["lesson_list_container_from_module"]["tag"]
                sel_attrs = cfg_selectors["lesson_list_container_from_module"].get("attrs", {})
                lesson_container_element = module_element.find(sel_tag, sel_attrs)
            
            if not lesson_container_element:
                print(f"  AVISO: Container de aulas não encontrado para o módulo '{module_title}'.")
                continue

            lesson_elements = self._find_elements_from_soup(lesson_container_element, cfg_selectors["lesson_item_selector_from_list"])
            
            for lesson_element in lesson_elements:
                overall_lesson_counter += 1
                lesson_title = self._get_text_from_element(lesson_element, cfg_selectors["lesson_title_selector_from_item"], f"Aula {overall_lesson_counter}")
                lesson_page_url = self._get_href_from_element(lesson_element, cfg_selectors.get("lesson_link_selector_from_item"), base_url=self.main_course_url)

                lesson_folder_name_with_prefix = f"{overall_lesson_counter:03d} - {lesson_title}"
                lesson_download_path = create_folder_structure(
                    self.base_output_path, self.course_name_for_folder, module_title, lesson_folder_name_with_prefix
                )
                if not lesson_download_path: continue # Pula se a pasta não pôde ser criada

                print(f"  Processando Aula {overall_lesson_counter:03d}: {lesson_title}")
                print(f"    Pasta: {lesson_download_path}")

                if not lesson_page_url:
                    print("    AVISO: Link da página da aula não encontrado.")
                    all_lessons_info.append({"title": lesson_title, "module": module_title, "error": "No lesson page URL"})
                    continue
                
                print(f"    Acessando página da aula: {lesson_page_url} ...")
                time.sleep(self.config.get("delay_between_lesson_pages", 0.5)) # Pausa configurável
                
                response_lesson_page = self._make_request(lesson_page_url, extra_headers={'Referer': self.main_course_url})
                if not response_lesson_page or response_lesson_page.status_code != 200:
                    print(f"    AVISO: Falha ao acessar a página da aula: {lesson_page_url}")
                    all_lessons_info.append({"title": lesson_title, "module": module_title, "lesson_page_url": lesson_page_url, "error": "Failed to fetch lesson page"})
                    continue
                
                soup_lesson_page = BeautifulSoup(response_lesson_page.text, 'html.parser')

                # Baixar Materiais de Apoio
                print("    Procurando materiais de apoio...")
                found_materials_for_lesson = False
                for mat_sel_config in cfg_selectors.get("material_link_selectors_on_lesson_page", []):
                    # Lógica para lidar com diferentes tipos de seletores de material (direto ou parent>item)
                    material_elements_to_search_in = soup_lesson_page
                    current_material_item_selector = mat_sel_config
                    
                    if mat_sel_config.get("parent_selector") and mat_sel_config.get("item_selector"):
                        parent_elements = self._find_elements_from_soup(soup_lesson_page, mat_sel_config["parent_selector"])
                        for parent_el in parent_elements:
                            material_elements_to_search_in = parent_el # Busca dentro do pai
                            current_material_item_selector = mat_sel_config["item_selector"]
                            material_links = self._find_elements_from_soup(material_elements_to_search_in, current_material_item_selector)
                            for mat_link_tag in material_links:
                                material_url = self._get_href_from_element(mat_link_tag, base_url=lesson_page_url)
                                material_name = sanitize_filename(mat_link_tag.get_text(strip=True) or f"material_anexo_{time.time()}")
                                if material_url:
                                    self._download_file(material_url, material_name, lesson_download_path, file_type="Material")
                                    found_materials_for_lesson = True
                        continue # Próxima config de material
                    
                    # Se for um seletor direto de links de material
                    material_links = self._find_elements_from_soup(material_elements_to_search_in, current_material_item_selector)
                    for mat_link_tag in material_links:
                        material_url = self._get_href_from_element(mat_link_tag, base_url=lesson_page_url) # href direto da tag
                        material_name = sanitize_filename(mat_link_tag.get_text(strip=True) or f"material_anexo_{time.time()}")
                        if material_url:
                            self._download_file(material_url, material_name, lesson_download_path, file_type="Material")
                            found_materials_for_lesson = True
                
                if not found_materials_for_lesson:
                    print("    Nenhum material de apoio encontrado ou configurado para esta aula.")

                # Encontrar e Baixar Vídeo
                video_source_url = self._extract_video_url_from_lesson_page(soup_lesson_page, lesson_page_url)
                if video_source_url:
                    print(f"      URL de vídeo/player encontrada: {video_source_url}")
                    self._download_video_with_yt_dlp(video_source_url, lesson_title, lesson_download_path, referer_url=lesson_page_url)
                else:
                    print("      AVISO: Nenhuma URL de vídeo/player encontrada para yt-dlp nesta página de aula.")

        print(f"\n--- Processamento do curso '{self.course_name_for_folder}' concluído. ---")


    def _extract_video_url_from_lesson_page(self, soup_lesson_page, lesson_page_url):
        """Tenta extrair a URL do vídeo da página da aula usando seletores da config."""
        for iframe_sel_config in self.config["selectors"].get("video_iframe_selectors_on_lesson_page", []):
            iframe_tag = soup_lesson_page.find(iframe_sel_config["tag"], iframe_sel_config.get("attrs", {}))
            if iframe_tag:
                video_src = iframe_tag.get("src")
                if video_src:
                    # Checagem especial para src_contains, se presente na config do seletor
                    if iframe_sel_config.get("attrs", {}).get("src_contains"):
                        if iframe_sel_config["attrs"]["src_contains"] in video_src:
                            return urljoin(lesson_page_url, video_src)
                    else: # Se não houver src_contains, retorna o src diretamente
                        return urljoin(lesson_page_url, video_src)
                
                # Checagem especial para data attributes, se presente na config do seletor
                vimeo_id_attr_name = iframe_sel_config.get("attrs", {}).get("vimeo_id_from_data_attr")
                if vimeo_id_attr_name and iframe_tag.get(vimeo_id_attr_name):
                    return f"https://player.vimeo.com/video/{iframe_tag.get(vimeo_id_attr_name)}"
        return None


    def _download_file(self, file_url, file_name_base, download_path, file_type="Arquivo"):
        """Baixa um arquivo genérico (usado para materiais)."""
        try:
            # Tenta obter uma extensão mais precisa
            _, guessed_ext = os.path.splitext(file_url.split('?')[0].split('#')[0])
            if not guessed_ext or len(guessed_ext) > 5 or len(guessed_ext) < 2:
                 # Heurística para nome de material (ex: "Slides Aula 1.pdf")
                base_name_for_ext, ext_from_name = os.path.splitext(file_name_base)
                if ext_from_name and len(ext_from_name) > 1 and len(ext_from_name) < 6:
                    guessed_ext = ext_from_name
                    file_name_base = base_name_for_ext # Usa o nome sem a extensão original
                else:
                    guessed_ext = ".dat" # Default

            file_name_with_ext = f"{sanitize_filename(file_name_base)}{guessed_ext}"
            file_path = os.path.join(download_path, file_name_with_ext)

            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"        {file_type} '{file_name_with_ext}' já existe. Pulando.")
                return

            print(f"        Baixando {file_type}: {file_name_with_ext} de {file_url}")
            response = self._make_request(file_url, stream=True, timeout=60) # Aumenta timeout para arquivos
            if response and response.status_code == 200 :
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=81920): # Chunk maior para arquivos
                        f.write(chunk)
                print(f"        {file_type} '{file_name_with_ext}' baixado.")
            else:
                print(f"        Falha ao baixar {file_type}: {file_name_base}. Status: {response.status_code if response else 'N/A'}")
        except Exception as e:
            print(f"        Erro ao baixar {file_type} '{file_name_base}': {e}")


    def _download_video_with_yt_dlp(self, video_player_url, lesson_title, download_path, referer_url):
        """Chama o yt-dlp para baixar o vídeo."""
        clean_lesson_title = sanitize_filename(lesson_title)
        # yt-dlp determinará a extensão. Usamos um placeholder que ele entende.
        video_filepath_template = os.path.join(download_path, f"{clean_lesson_title}.%(ext)s")

        # Checa se o vídeo já existe com extensões comuns (yt-dlp pode escolher mp4, mkv, webm etc.)
        video_exists = False
        possible_extensions = ['.mp4', '.mkv', '.webm', '.flv', '.avi', '.mov', '.ts']
        for ext_check in possible_extensions:
            # Verifica o nome do arquivo base sanitizado + extensão
            if os.path.exists(os.path.join(download_path, f"{clean_lesson_title}{ext_check}")):
                video_exists = True
                print(f"        Vídeo '{clean_lesson_title}{ext_check}' parece já existir. Pulando.")
                break
        
        if not video_exists:
            print(f"        Iniciando download do vídeo: {clean_lesson_title} (de {video_player_url})")
            try:
                command = [
                    self.yt_dlp_path,
                    '--referer', referer_url,
                    '-o', video_filepath_template,
                    '--no-playlist',
                    '--force-overwrites', # Se um download parcial falhou, tenta de novo
                    '--retries', '3',
                    '--fragment-retries', '3',
                    '--socket-timeout', '60',
                    '--progress',
                    '--no-warnings',
                    # Sem -f, deixa yt-dlp escolher o melhor.
                    # Para forçar qualidade e formato (ex: melhor mp4 até 1080p):
                    # '-f', 'bestvideo[height<=?1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=?1080][ext=mp4]/best[height<=?1080]',
                    video_player_url
                ]
                print(f"        Executando: {' '.join(command)}")
                subprocess.run(command, check=True) # check=True fará o script parar se yt-dlp retornar erro
                print(f"        Download do vídeo '{clean_lesson_title}' concluído.")
            except FileNotFoundError:
                print(f"        ERRO CRÍTICO: '{self.yt_dlp_path}' não encontrado. Verifique a instalação e YT_DLP_PATH.")
            except subprocess.CalledProcessError as e:
                print(f"        ERRO no yt-dlp para '{clean_lesson_title}': {e.returncode}")
            except Exception as e:
                print(f"        Erro inesperado no download do vídeo '{clean_lesson_title}': {e}")