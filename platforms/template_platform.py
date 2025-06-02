"""
MODELO DE ADAPTADOR DE PLATAFORMA (TEMPLATE_PLATFORM_ADAPTER)
--------------------------------------------------------------

Instruções para criar um novo adaptador para uma plataforma de curso:
1. Copie este arquivo (`template_platform.py`) para a mesma pasta `platforms/`.
2. Renomeie a cópia para algo descritivo da plataforma (ex: `minha_escola_adapter.py`).
   O nome do arquivo (sem o '.py') será usado para invocar este adaptador via linha de comando.
3. Edite o dicionário `PLATFORM_ADAPTER_CONFIG` abaixo com os detalhes específicos da nova plataforma.
   - Use as "Ferramentas de Desenvolvedor" do seu navegador (geralmente F12) para
     inspecionar as páginas da plataforma e encontrar os seletores CSS, URLs,
     nomes dos campos de formulário HTML, etc.
   - Para seletores, a estrutura esperada é um dicionário:
     `{"tag": "nome_da_tag_html", "attrs": {"atributo1": "valor1", "id": "id_do_elemento", "class_": "classe_css"}}`
     Onde "attrs" é opcional. "class_" é usado em vez de "class" por ser uma palavra reservada em Python.
     Se um seletor CSS mais complexo for necessário (ex: `div.content > p.important`), você pode
     precisar adaptar a lógica no `downloader_engine.py` ou usar uma função customizada.
     Por enquanto, o motor espera seletores mais diretos para tag e atributos.

Exemplos de Seletores (baseados no que vimos para o CEI, APENAS COMO EXEMPLO ILUSTRATIVO):
- Para o container de módulos: `{"tag": "div", "attrs": {"id": "ef-modules"}}`
- Para um item de módulo: `{"tag": "div", "attrs": {"class_": "accordion-item ef-classes-accordion"}}`
- Para o título do módulo (dentro do item de módulo): `{"tag": "button", "attrs": {"class_": "accordion-button"}}` (e então pegar o texto da div interna)
- Para um item de aula (dentro da lista de aulas de um módulo): `{"tag": "li", "attrs": {"class_": "ef-class-item"}}`
- Para o link da aula (dentro do item de aula): `{"tag": "a"}` (para pegar o href)
- Para o título da aula (dentro do link da aula): `{"tag": "span", "attrs": {"class_": "ef-class-name"}}`
- Para o iframe do vídeo na página da aula: `{"tag": "iframe", "attrs": {"id": "ef-video"}}`
- Para o container de materiais (se for um dropdown): `{"tag": "div", "attrs": {"class_": "dropdown"}}`
  (o motor então buscaria `a.dropdown-item` dentro disso)
"""

PLATFORM_ADAPTER_CONFIG = {
    "platform_name": "NomeDaSuaPlataforma (Ex: PortalExemploEdu)",

    "login_page_url": "https://site.exemplo.com/login", 
    "login_form_action_url": "https://site.exemplo.com/efetuar_login", 
    
    "login_payload_fields": {
        "username": "email_ou_usuario_no_html", 
        "password": "senha_no_html",              
    },
   
    "login_success_indicators": [
        {"type": "url_contains", "value": "/painel"},       
        {"type": "url_is_not", "value": "https://site.exemplo.com/login"}, 
        {"type": "page_text_contains", "value": "Bem-vindo(a) de volta"}, 
    ],

    "login_failure_indicators": [ 
        {"type": "page_text_contains", "value": "Usuário ou senha inválidos"},
        {"type": "page_text_contains", "value": "Falha na autenticação"},
    ],


    "module_item_selector": {"tag": "div", "attrs": {"class_": "nome-da-classe-para-cada-modulo"}},
    "module_title_selector_from_item": {"tag": "h2", "attrs": {"class_": "titulo-do-modulo"}},
 
    "lesson_list_container_from_module": {"tag": "ul", "attrs": {"class_": "container-das-aulas-do-modulo"}},
    "lesson_item_selector_from_list": {"tag": "li", "attrs": {"class_": "item-de-uma-aula"}}, 

    "lesson_title_selector_from_item": {"tag": "span", "attrs": {"class_": "nome-da-aula"}},
    "lesson_link_selector_from_item": {"tag": "a", "attrs": {"class_": "link-para-pagina-da-aula"}},

    "video_iframe_selectors_on_lesson_page": [
        {"tag": "iframe", "attrs": {"id": "id_do_player_de_video"}},
        {"tag": "iframe", "attrs": {"class_": "classe_do_iframe_vimeo"}},
        {"tag": "iframe", "attrs": {"src_contains": "player.vimeo.com/video/"}}, # Para Vimeo
        {"tag": "iframe", "attrs": {"src_contains": "youtube.com/embed/"}},    # Para YouTube
    ],


    "material_link_selectors_on_lesson_page": [
        {"tag": "a", "attrs": {"class_": "link-pdf-material"}},
        {"tag": "a", "attrs": {"class_": "download-apostila"}},
    ],


}