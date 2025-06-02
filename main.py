import importlib 
import argparse  
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
from downloader_engine import CoreDownloader


def main():
    parser = argparse.ArgumentParser(
        description="Framework Genérico para Baixar Materiais de Cursos Online.",
        epilog="Exemplo de uso: python main.py meu_adapter_plataforma https://site.com/curso/meu-curso 'Nome do Curso Para Pasta' 'meuemail@example.com' 'minhasenha123' -o G:/Meu Drive/Cursos"
    )
    parser.add_argument(
        "platform_adapter_module_name", 
        help="Nome do arquivo do adaptador da plataforma na pasta 'platforms' (ex: 'template_platform' ou 'minha_escola_adapter', sem o '.py')"
    )
    parser.add_argument(
        "target_course_page_url", 
        help="URL da página principal do curso específico que você quer baixar (onde os módulos/aulas são listados)."
    )
    parser.add_argument(
        "course_name_for_folder", 
        help="Nome que será usado para criar a pasta principal deste curso."
    )
    parser.add_argument("username", help="Seu nome de usuário ou e-mail para login na plataforma.")
    parser.add_argument("password", help="Sua senha para login na plataforma.")
    
    parser.add_argument(
        "-o", "--output_base_directory", 
        default=".", 
        help="Diretório base onde a pasta do curso será criada (padrão: pasta atual do script)."
    )
    parser.add_argument(
        "--yt_dlp_path", 
        default=None, 
        help="Caminho completo para o executável yt-dlp (se não estiver no PATH do sistema)."
    )
    parser.add_argument(
        "--skip_videos",
        action="store_true", 
        help="Pular o download de vídeos, baixando apenas materiais de apoio."
    )
    parser.add_argument(
        "--skip_materials",
        action="store_true",
        help="Pular o download de materiais de apoio, baixando apenas vídeos."
    )


    args = parser.parse_args()

    try:
        adapter_module = importlib.import_module(f"platforms.{args.platform_adapter_module_name}")
        platform_config = adapter_module.PLATFORM_ADAPTER_CONFIG
    except ImportError as e:
        print(f"Erro: Não foi possível carregar o adaptador de plataforma '{args.platform_adapter_module_name}'.")
        print(f"Verifique se o arquivo 'platforms/{args.platform_adapter_module_name}.py' existe e não contém erros de importação.")
        print(f"Detalhe do erro: {e}")
        return
    except AttributeError:
        print(f"Erro: O arquivo adaptador 'platforms/{args.platform_adapter_module_name}.py' não define corretamente a variável 'PLATFORM_ADAPTER_CONFIG'.")
        return

    print(f"Usando adaptador para: {platform_config.get('platform_name', args.platform_adapter_module_name)}")

    absolute_output_base_dir = os.path.abspath(args.output_base_directory)
    print(f"Diretório base para downloads: {absolute_output_base_dir}")


    engine = CoreDownloader(
        platform_config=platform_config,
        base_output_path=absolute_output_base_dir,
        course_url=args.target_course_page_url, 
        course_name_for_folder=args.course_name_for_folder,
        yt_dlp_path=args.yt_dlp_path
    )


    if engine.login(args.username, args.password):
        print(f"Login realizado com sucesso para {platform_config.get('platform_name')}.")
        engine.process_course() 
    else:
        print(f"Falha no login para {platform_config.get('platform_name')}. Verifique as credenciais e a configuração do adaptador.")

if __name__ == '__main__':
    main()