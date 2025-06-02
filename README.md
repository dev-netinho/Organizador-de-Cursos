# SEU_NOME_DE_PROJETO_AQUI (Ex: OrganizadorDeAulasOnline)

Um framework Python genérico e configurável para baixar materiais de apoio e, opcionalmente, vídeos de plataformas de cursos online.

**AVISO:** Este script é fornecido para fins educacionais e para ajudar usuários a acessarem conteúdo que já possuem direito de acesso para uso offline pessoal. Respeite os Termos de Serviço das plataformas de curso. O download não autorizado de conteúdo protegido por direitos autorais é ilegal. Use com responsabilidade.

## Funcionalidades (Planejadas/Em Desenvolvimento)

* Login em plataformas de curso.
* Navegação e identificação da estrutura de cursos (módulos, aulas).
* Download de materiais de apoio (PDFs, slides, etc.).
* Download de vídeos das aulas (usando `yt-dlp` como backend).
* Organização dos arquivos baixados em uma estrutura de pastas lógica.
* Design modular para fácil adaptação a novas plataformas através de "Adaptadores de Plataforma".

## Pré-requisitos

* Python 3.7+
* `pip` (gerenciador de pacotes Python)
* `yt-dlp`: Esta ferramenta precisa ser instalada separadamente e estar no PATH do sistema, ou o caminho para seu executável deve ser fornecido via argumento de linha de comando.
    * Instalação: `pip install yt-dlp` ou siga as instruções em [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
* `ffmpeg`: Necessário para o `yt-dlp` juntar áudio e vídeo em muitos casos. Deve estar instalado e no PATH.
    * Download: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Instalação das Dependências Python

Na pasta raiz do projeto, execute:
```bash
pip install -r requirements.txt# Organizador-de-Cursos
# Organizador-de-Cursos
