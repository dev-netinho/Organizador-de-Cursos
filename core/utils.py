# core/utils.py
import re
import os

def sanitize_filename(filename, max_length=150):
    """
    Limpa e sanitiza um nome de arquivo, removendo caracteres inválidos
    e limitando o comprimento.
    """
    if not filename:
        return "arquivo_sem_titulo"
    
    sanitized = str(filename)
    # Remove caracteres problemáticos para Windows, Linux, macOS
    sanitized = re.sub(r'[\\/*?:"<>|#%&{}$!@()+=\[\]]', "", sanitized) 

    sanitized = re.sub(r'[\s._-]+', ' ', sanitized).strip() 

    sanitized = sanitized.strip('. ')
    
    return sanitized[:max_length] if sanitized else "arquivo_sanitizado_sem_titulo"

def create_folder_structure(base_output_path, course_name_for_folder, module_name, lesson_name_with_prefix):
    """
    Cria a estrutura de pastas: base_output_path/curso/modulo/aula.
    Retorna o caminho completo para a pasta da aula.
    """
    s_course_name = sanitize_filename(course_name_for_folder)
    s_module_name = sanitize_filename(module_name)
    s_lesson_name = sanitize_filename(lesson_name_with_prefix)

    course_folder_path = os.path.join(base_output_path, s_course_name)
    module_folder_path = os.path.join(course_folder_path, s_module_name)
    lesson_folder_path = os.path.join(module_folder_path, s_lesson_name)

    try:
        os.makedirs(lesson_folder_path, exist_ok=True)
        return lesson_folder_path
    except OSError as e:
        print(f"Erro ao criar a estrutura de pastas '{lesson_folder_path}': {e}")

        lesson_folder_path_alt = os.path.join(module_folder_path, sanitize_filename(f"aula_{lesson_name_with_prefix.split(' ')[0]}"))
        try:
            os.makedirs(lesson_folder_path_alt, exist_ok=True)
            print(f"Usando caminho alternativo para aula: {lesson_folder_path_alt}")
            return lesson_folder_path_alt
        except Exception as e_alt:
            print(f"Erro ao criar caminho alternativo para aula: {e_alt}. Pulando criação de pasta para esta aula.")
            return None 