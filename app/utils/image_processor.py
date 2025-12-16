"""
Módulo principal de processamento de imagem
Responsável por download, manipulação, renderização de textos e salvamento
"""
import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from app import config
from app.utils.logger import get_logger
from app.utils.task_manager import task_manager
from app.utils.validators import validate_product_data

logger = get_logger(__name__)

class ImageProcessor:
    """Processador de imagens com suporte a múltiplos produtos"""
    
    def __init__(self):
        self.fonts = self._load_fonts()
        # Configs dinâmicas (serão sobrescritas a cada processo se recebidas)
        self.layout_config = None
        self.theme_config = None
        self.desconto_a_vista = 5  # Default 5%
    
    def _get_font_path(self, font_name=None):
        """Retorna o caminho da fonte baseado no nome"""
        if font_name:
            font_file = f"{font_name}.ttf"
            font_path = os.path.join(config.FONTS_DIR, font_file)
            if os.path.exists(font_path):
                return font_path
            # Tentar variações comuns
            variations = [f"{font_name}bd.ttf", f"{font_name.lower()}.ttf"]
            for var in variations:
                var_path = os.path.join(config.FONTS_DIR, var)
                if os.path.exists(var_path):
                    return var_path
        return config.DEFAULT_FONT_PATH
    
    def _load_fonts_with_config(self, layout_config=None, theme_config=None):
        """Carrega fontes com tamanhos dinâmicos baseados em layout_config"""
        fonts = {}
        
        # Determinar tamanhos das fontes
        if layout_config:
            desc_size = layout_config.get('fonteDescricao', config.FONT_DESCRIPTION_SIZE)
            ref_size = layout_config.get('fonteReferencia', config.FONT_REF_SIZE_PROMO)
            price_size = layout_config.get('fontePreco', config.FONT_PRICE_SIZE)
            esgotado_size = layout_config.get('fonteEsgotado', config.FONT_ESGOTADO_SIZE)
        else:
            desc_size = config.FONT_DESCRIPTION_SIZE
            ref_size = config.FONT_REF_SIZE_PROMO
            price_size = config.FONT_PRICE_SIZE
            esgotado_size = config.FONT_ESGOTADO_SIZE
        
        # Determinar fonte a usar
        font_name = theme_config.get('fonte', 'arial') if theme_config else 'arial'
        font_path = self._get_font_path(font_name)
        
        try:
            if os.path.exists(font_path):
                fonts['description'] = ImageFont.truetype(font_path, desc_size)
                fonts['ref_promo'] = ImageFont.truetype(font_path, ref_size)
                fonts['price'] = ImageFont.truetype(font_path, price_size)
                fonts['esgotado'] = ImageFont.truetype(font_path, esgotado_size)
                logger.info(f"Fontes carregadas: {font_path} (desc={desc_size}, price={price_size})")
            else:
                logger.warning(f"Fonte não encontrada em {font_path}. Usando fonte padrão.")
                fonts['description'] = ImageFont.load_default()
                fonts['ref_promo'] = ImageFont.load_default()
                fonts['price'] = ImageFont.load_default()
                fonts['esgotado'] = ImageFont.load_default()
        except Exception as e:
            logger.error(f"Erro ao carregar fontes: {e}. Usando fonte padrão.")
            fonts['description'] = ImageFont.load_default()
            fonts['ref_promo'] = ImageFont.load_default()
            fonts['price'] = ImageFont.load_default()
            fonts['esgotado'] = ImageFont.load_default()
        
        return fonts
    
    def _get_padding_x(self):
        """Retorna padding X interno do bloco (usa layout_config se disponível)"""
        if self.layout_config:
            return self.layout_config.get('blocoPaddingX', config.PADDING_X)
        return config.PADDING_X
    
    def _get_bloco_x(self):
        """Retorna posição X do início do bloco (distância da borda esquerda)"""
        if self.layout_config:
            return self.layout_config.get('blocoX', config.PADDING_X)
        return config.PADDING_X
    
    def _get_bloco_padding_y(self):
        """Retorna padding Y interno do bloco (usa layout_config se disponível)"""
        if self.layout_config:
            return self.layout_config.get('blocoPaddingY', 8)
        return 8  # Valor padrão original
    
    def _get_padding_y(self):
        """Retorna padding Y - distância da borda inferior (usa layout_config se disponível)"""
        if self.layout_config:
            return self.layout_config.get('blocoY', config.PADDING_Y)
        return config.PADDING_Y
    
    def _get_block_spacing(self):
        """Retorna espaçamento entre blocos (usa layout_config se disponível)"""
        if self.layout_config:
            return self.layout_config.get('blocoEspacamento', config.BLOCK_SPACING)
        return config.BLOCK_SPACING
    
    def _get_line_height(self):
        """Retorna multiplicador de altura de linha (usa layout_config se disponível)"""
        if self.layout_config:
            return self.layout_config.get('linhaAltura', config.LINE_HEIGHT_MULTIPLIER)
        return config.LINE_HEIGHT_MULTIPLIER
    
    def _parse_rgba(self, rgba_str):
        """Converte string rgba(r, g, b, a) para tupla (r, g, b, a)"""
        if not rgba_str or not isinstance(rgba_str, str):
            return None
        try:
            # rgba(220, 20, 60, 0.86)
            rgba_str = rgba_str.replace('rgba(', '').replace(')', '')
            parts = [p.strip() for p in rgba_str.split(',')]
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = int(float(parts[3]) * 255)  # Converter 0-1 para 0-255
            return (r, g, b, a)
        except:
            return None
    
    def _get_promo_bg_color(self):
        """Retorna cor de fundo para promoção (usa theme_config se disponível)"""
        if self.theme_config:
            color = self._parse_rgba(self.theme_config.get('corFundoPromocao'))
            if color:
                return color
        return config.COLOR_PROMO_BACKGROUND
    
    def _get_normal_bg_color(self):
        """Retorna cor de fundo normal (usa theme_config se disponível)"""
        if self.theme_config:
            color = self._parse_rgba(self.theme_config.get('corFundoPadrao'))
            if color:
                return color
        return config.COLOR_NORMAL_BACKGROUND
    
    def _get_promo_text_color(self):
        """Retorna cor de texto para promoção (usa theme_config se disponível)"""
        if self.theme_config:
            color = self._parse_rgba(self.theme_config.get('corTextoPromocao'))
            if color:
                return color[:3]  # RGB sem alpha para texto
        return config.COLOR_TEXT_WHITE
    
    def _get_normal_text_color(self):
        """Retorna cor de texto normal (usa theme_config se disponível)"""
        if self.theme_config:
            color = self._parse_rgba(self.theme_config.get('corTextoPadrao'))
            if color:
                return color[:3]  # RGB sem alpha para texto
        return config.COLOR_TEXT_WHITE
    
    def _load_fonts(self):
        """Carrega as fontes TrueType necessárias"""
        fonts = {}
        
        try:
            if os.path.exists(config.DEFAULT_FONT_PATH):
                fonts['description'] = ImageFont.truetype(config.DEFAULT_FONT_PATH, config.FONT_DESCRIPTION_SIZE)
                fonts['ref_promo'] = ImageFont.truetype(config.DEFAULT_FONT_PATH, config.FONT_REF_SIZE_PROMO)
                fonts['price'] = ImageFont.truetype(config.DEFAULT_FONT_PATH, config.FONT_PRICE_SIZE)
                fonts['esgotado'] = ImageFont.truetype(config.DEFAULT_FONT_PATH, config.FONT_ESGOTADO_SIZE)
                logger.info(f"Fontes carregadas de: {config.DEFAULT_FONT_PATH}")
            else:
                logger.warning(f"Fonte não encontrada em {config.DEFAULT_FONT_PATH}. Usando fonte padrão.")
                fonts['description'] = ImageFont.load_default()
                fonts['ref_promo'] = ImageFont.load_default()
                fonts['price'] = ImageFont.load_default()
                fonts['esgotado'] = ImageFont.load_default()
        except Exception as e:
            logger.error(f"Erro ao carregar fontes: {e}. Usando fonte padrão.")
            fonts['description'] = ImageFont.load_default()
            fonts['ref_promo'] = ImageFont.load_default()
            fonts['price'] = ImageFont.load_default()
            fonts['esgotado'] = ImageFont.load_default()
        
        return fonts
    
    def _download_image(self, url):
        """
        Download de imagem de uma URL
        
        Args:
            url (str): URL da imagem
        
        Returns:
            PIL.Image: Imagem carregada
        
        Raises:
            Exception: Se falhar no download
        """
        logger.info(f"Iniciando download de: {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            image_bytes = BytesIO(response.content)
            image = Image.open(image_bytes).convert("RGBA")
            
            logger.info(f"Imagem baixada com sucesso: {image.size}")
            return image
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar imagem {url}: {e}")
            raise
    
    def _format_numeracao_utilizada(self, numeracao_raw):
        """
        Formata a numeração utilizada, removendo duplicações como "52 (52)" -> "52"
        
        Args:
            numeracao_raw (str): Numeração original (pode ser "G3 (52/54)" ou "52 (52)")
        
        Returns:
            str: Numeração formatada sem duplicação
        """
        import re
        
        # Se não tem parênteses, retorna como está
        if '(' not in numeracao_raw:
            return numeracao_raw
        
        # Extrair parte antes e dentro dos parênteses
        match = re.match(r'^(.+?)\s*\((.+?)\)$', numeracao_raw.strip())
        if not match:
            return numeracao_raw
        
        antes = match.group(1).strip()
        dentro = match.group(2).strip()
        
        # Se são iguais (ex: "52 (52)"), retorna apenas um
        if antes == dentro:
            return antes
        
        # Se diferentes (ex: "G3 (52/54)"), mantém o formato original
        return numeracao_raw
    
    def _apply_theme(self, base_image, theme_image):
        """
        Aplica tema na imagem base
        
        Args:
            base_image (PIL.Image): Imagem base
            theme_image (PIL.Image): Imagem de tema
        
        Returns:
            PIL.Image: Imagem com tema aplicado
        """
        logger.info("Aplicando tema")
        
        try:
            theme_image = theme_image.convert("RGBA")
            base_width, base_height = base_image.size
            
            # Redimensionar tema para o tamanho exato da imagem original
            theme_image = theme_image.resize((base_width, base_height), Image.Resampling.LANCZOS)
            
            # Criar imagem temporária para composição
            temp_composite = Image.new("RGBA", base_image.size)
            temp_composite.paste(base_image, (0, 0))
            temp_composite.paste(theme_image, (0, 0), theme_image)
            
            logger.info("Tema aplicado com sucesso")
            return temp_composite
        except Exception as e:
            logger.error(f"Erro ao aplicar tema: {e}")
            raise
    
    def _extract_dominant_color(self, image, region_y_start, region_y_end, product_description=""):
        """
        Extrai a cor predominante de uma região específica da imagem baseada no tipo de produto
        
        Args:
            image (PIL.Image): Imagem original
            region_y_start (float): Posição Y inicial da região (0-1, percentual)
            region_y_end (float): Posição Y final da região (0-1, percentual)
            product_description (str): Descrição do produto para identificar se é peça superior ou inferior
        
        Returns:
            tuple: (cor_fundo, cor_texto) - ambas em formato (R, G, B, A)
        """
        try:
            width, height = image.size
            
            # Definir retângulo central vertical (corpo da modelo)
            # Horizontal: 30%-70% da largura (40% central)
            body_x_start = int(width * 0.30)
            body_x_end = int(width * 0.70)
            
            # Vertical: desprezar 15% superior (cabeça) e 10% inferior (pés)
            body_y_start = int(height * 0.15)
            body_y_end = int(height * 0.90)
            
            # Recortar retângulo do corpo
            body_region = image.crop((body_x_start, body_y_start, body_x_end, body_y_end))
            body_height = body_region.height
            
            # Identificar tipo de produto (superior ou inferior)
            description_upper = product_description.upper()
            top_keywords = ['BLUSA', 'T-SHIRT', 'CROPPED', 'CAMISA', 'BLAZER', 'CASACO', 'JAQUETA', 'TOP', 'REGATA']
            bottom_keywords = ['CALÇA', 'SHORT', 'SAIA', 'BERMUDA', 'PANTALONA', 'LEGGING']
            
            is_top = any(keyword in description_upper for keyword in top_keywords)
            is_bottom = any(keyword in description_upper for keyword in bottom_keywords)
            
            # Determinar região dentro do corpo para análise
            if is_top:
                # Parte superior: primeiros 45% do corpo
                sample_y_start = 0
                sample_y_end = int(body_height * 0.45)
                logger.info(f"🔍 Produto identificado como SUPERIOR - analisando topo do corpo")
            elif is_bottom:
                # Parte inferior: últimos 55% do corpo
                sample_y_start = int(body_height * 0.45)
                sample_y_end = body_height
                logger.info(f"🔍 Produto identificado como INFERIOR - analisando parte baixa do corpo")
            else:
                # Não identificado: usar região completa do corpo
                sample_y_start = 0
                sample_y_end = body_height
                logger.info(f"⚠️ Tipo de produto não identificado - analisando corpo inteiro")
            
            # Recortar região de amostragem
            sample_region = body_region.crop((0, sample_y_start, body_region.width, sample_y_end))
            
            # Redimensionar para análise
            region_small = sample_region.resize((150, 150), Image.Resampling.LANCZOS)
            
            # Converter para RGB se necessário
            if region_small.mode != 'RGB':
                region_small = region_small.convert('RGB')
            
            # Obter pixels
            pixels = list(region_small.getdata())
            
            # Filtrar cores extremas
            filtered_pixels = [
                p for p in pixels
                if 80 < sum(p) < 700
            ]
            
            if len(filtered_pixels) < len(pixels) * 0.3:
                filtered_pixels = pixels
            
            # Quantizar para encontrar cores dominantes
            temp_img = Image.new('RGB', (len(filtered_pixels), 1))
            temp_img.putdata(filtered_pixels)
            quantized = temp_img.quantize(colors=16, method=2)
            palette_image = quantized.convert('RGB')
            
            # Contar frequência de cada cor
            quantized_pixels = list(palette_image.getdata())
            color_count = {}
            for pixel in quantized_pixels:
                if pixel in color_count:
                    color_count[pixel] += 1
                else:
                    color_count[pixel] = 1
            
            # Pegar a cor mais frequente
            dominant_color = max(color_count.items(), key=lambda x: x[1])[0]
            avg_r, avg_g, avg_b = dominant_color
            
            logger.info(f"🎨 Cor original detectada: RGB({avg_r}, {avg_g}, {avg_b})")
            
            # Calcular luminosidade (0-255)
            luminosity = (0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b)
            
            # Determinar se é cor clara (luminosidade > 180)
            is_light_color = luminosity > 180
            
            if is_light_color:
                # Fundo claro: escurecer muito pouco e usar texto escuro
                bg_r = int(avg_r * 0.95)
                bg_g = int(avg_g * 0.95)
                bg_b = int(avg_b * 0.95)
                text_color = (40, 40, 40, 255)  # Texto quase preto
                logger.info(f"💡 Cor CLARA detectada (luminosidade: {luminosity:.0f}) - usando texto escuro")
            else:
                # Fundo escuro: escurecer 40% e usar texto branco
                bg_r = int(avg_r * 0.60)
                bg_g = int(avg_g * 0.60)
                bg_b = int(avg_b * 0.60)
                text_color = (255, 255, 255, 255)  # Texto branco
                logger.info(f"🌙 Cor ESCURA detectada (luminosidade: {luminosity:.0f}) - usando texto branco")
            
            # Adicionar opacidade (180 = ~70% opaco)
            background_color = (bg_r, bg_g, bg_b, 180)
            
            return (background_color, text_color)
            
        except Exception as e:
            logger.warning(f"Erro ao extrair cor predominante: {e}. Usando cor padrão.")
            # Fallback para preto semi-transparente com texto branco
            return ((0, 0, 0, 150), (255, 255, 255, 255))
    
    def _calculate_text_bbox(self, draw, text, font):
        """
        Calcula a caixa delimitadora de um texto
        Compatível com diferentes versões do Pillow
        """
        try:
            # Tenta a API mais recente (Pillow 8.0+)
            bbox = draw.textbbox((0, 0), text, font=font)
        except (AttributeError, TypeError):
            # Fallback para versões antigas
            width, height = draw.textsize(text, font=font)
            bbox = (0, 0, width, height)
        
        return bbox
    
    def _draw_text_with_shadow(self, draw, position, text, font, fill, shadow=True):
        """
        Desenha texto com sombra para melhor legibilidade
        
        Args:
            draw: Objeto de desenho
            position: Tupla (x, y)
            text: Texto a desenhar
            font: Fonte
            fill: Cor do texto
            shadow: Se deve desenhar sombra
        """
        if shadow:
            # Desenhar sombra primeiro (offset)
            shadow_pos = (position[0] + config.TEXT_SHADOW_OFFSET, position[1] + config.TEXT_SHADOW_OFFSET)
            draw.text(shadow_pos, text, font=font, fill=config.TEXT_SHADOW_COLOR)
        
        # Desenhar texto principal
        draw.text(position, text, font=font, fill=fill)
    
    def _format_price_text(self, price):
        """Formata preço para formato brasileiro (R$ X.XXX,XX)"""
        return f"R${price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def _split_description(self, description, max_width, font, draw):
        """
        Divide a descrição em até 2 linhas se exceder a largura máxima
        
        Args:
            description (str): Texto da descrição
            max_width (int): Largura máxima em pixels
            font: Fonte a ser usada
            draw: Objeto de desenho
        
        Returns:
            list: Lista de linhas (1 ou 2 elementos)
        """
        # Verificar se cabe em uma linha
        bbox = self._calculate_text_bbox(draw, description, font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            return [description]
        
        # Dividir apenas por espaço (mantém palavras com hífen juntas)
        words = description.split()
        if len(words) <= 1:
            # Se for palavra única muito longa, dividir no meio
            mid = len(description) // 2
            return [description[:mid], description[mid:]]
        
        # Dividir em duas linhas otimizando o espaço
        mid_point = len(words) // 2
        line1 = ' '.join(words[:mid_point])
        line2 = ' '.join(words[mid_point:])
        
        return [line1, line2]
    
    def _calculate_min_width_for_product(self, draw, product, is_promotional=False):
        """
        Calcula a largura MÍNIMA necessária para um produto específico,
        baseada no texto mais largo de cada linha.
        
        Args:
            draw: Objeto de desenho
            product (dict): Dados do produto
            is_promotional (bool): Se é um produto promocional
        
        Returns:
            int: Largura mínima necessária em pixels (sem padding extra)
        """
        max_width = 0
        
        # 1. Descrição (pode ter 2 linhas)
        reference_text = "Tam: ESGOTADO"
        bbox_ref = self._calculate_text_bbox(draw, reference_text, self.fonts['description'])
        max_desc_width = bbox_ref[2] - bbox_ref[0]
        
        description_lines = self._split_description(product['DescricaoFinal'], max_desc_width, self.fonts['description'], draw)
        for line in description_lines:
            bbox = self._calculate_text_bbox(draw, line, self.fonts['description'])
            max_width = max(max_width, bbox[2] - bbox[0])
        
        # 2. Referência
        ref_text = f"Ref {product['Referencia']}"
        bbox = self._calculate_text_bbox(draw, ref_text, self.fonts['description'])
        max_width = max(max_width, bbox[2] - bbox[0])
        
        # 3. Tamanhos disponíveis
        if product['TamanhosDisponiveis'] and product['TamanhosDisponiveis'] != 'N/A':
            tam_text = f"Tam: {product['TamanhosDisponiveis']}"
            bbox = self._calculate_text_bbox(draw, tam_text, self.fonts['description'])
            max_width = max(max_width, bbox[2] - bbox[0])
        
        # 4. Usei (numeração utilizada) - formatada
        numeracao_formatada = self._format_numeracao_utilizada(product['NumeracaoUtilizada'])
        usei_text = f"Usei: {numeracao_formatada}"
        bbox = self._calculate_text_bbox(draw, usei_text, self.fonts['description'])
        max_width = max(max_width, bbox[2] - bbox[0])
        
        # 5. Preços
        if is_promotional and product['PrecoPromocional'] > 0:
            # DE R$XX,XX POR (fonte description)
            de_por_text = f"DE {self._format_price_text(product['Preco'])} POR"
            bbox = self._calculate_text_bbox(draw, de_por_text, self.fonts['description'])
            max_width = max(max_width, bbox[2] - bbox[0])
            
            # R$XX,XX no cartão (fonte price)
            promo_text = f"{self._format_price_text(product['PrecoPromocional'])} no cartão"
            bbox = self._calculate_text_bbox(draw, promo_text, self.fonts['price'])
            max_width = max(max_width, bbox[2] - bbox[0])
            
            # R$XX,XX à vista (fonte price)
            if product['PrecoPromocionalAVista'] > 0:
                vista_text = f"{self._format_price_text(product['PrecoPromocionalAVista'])} à vista"
                bbox = self._calculate_text_bbox(draw, vista_text, self.fonts['price'])
                max_width = max(max_width, bbox[2] - bbox[0])
        else:
            # Preço normal
            price_text = self._format_price_text(product['Preco'])
            bbox = self._calculate_text_bbox(draw, price_text, self.fonts['price'])
            max_width = max(max_width, bbox[2] - bbox[0])
        
        return int(max_width)
    
    def _calculate_uniform_block_width(self, draw, products, check_promotional=True):
        """
        Calcula a largura UNIFORME para todos os blocos de produtos.
        Encontra a maior largura mínima necessária entre todos os produtos.
        
        Args:
            draw: Objeto de desenho
            products (list): Lista de produtos
            check_promotional (bool): Se deve verificar se cada produto é promocional
        
        Returns:
            int: Largura uniforme para todos os blocos (com padding horizontal interno)
        """
        max_width = 0
        
        for product in products:
            is_promo = check_promotional and product['PrecoPromocional'] > 0
            width = self._calculate_min_width_for_product(draw, product, is_promo)
            max_width = max(max_width, width)
        
        # Adicionar padding horizontal interno (blocoPaddingX de cada lado)
        padding_x_interno = self._get_padding_x()
        block_width = max_width + (2 * padding_x_interno)
        logger.info(f"   📐 Largura bloco: texto={max_width}px + (2 * paddingX={padding_x_interno}) = {block_width}px")
        
        return int(block_width)
    
    def _calculate_dynamic_block_width(self, draw, product, is_promotional=False):
        """
        DEPRECATED: Mantido para compatibilidade.
        Use _calculate_uniform_block_width para largura uniforme entre produtos.
        
        Calcula a largura do bloco baseada no texto mais longo + padding
        Para produtos promocionais, considera "POR R$119,90 no cartão" como referência
        
        Args:
            draw: Objeto de desenho
            product (dict): Dados do produto
            is_promotional (bool): Se é um produto promocional
        
        Returns:
            int: Largura do bloco em pixels
        """
        if is_promotional:
            # Para promoção, usar o texto mais longo possível
            reference_texts = [
                "POR R$119,90 no cartão",  # Texto mais longo esperado
                "DE R$119,90",
                "R$119,90 à vista"
            ]
            max_text_width = 0
            for text in reference_texts:
                bbox = self._calculate_text_bbox(draw, text, self.fonts['price'])
                text_width = bbox[2] - bbox[0]
                max_text_width = max(max_text_width, text_width)
        else:
            # Texto de referência normal: "Tam: ESGOTADO"
            reference_text = "Tam: ESGOTADO"
            bbox = self._calculate_text_bbox(draw, reference_text, self.fonts['description'])
            max_text_width = bbox[2] - bbox[0]
        
        # Adicionar padding (2x PADDING_X para esquerda e direita)
        padding_x_interno = self._get_padding_x()
        block_width = max_text_width + (2 * padding_x_interno)
        logger.info(f"   📐 Largura bloco: texto={max_text_width}px + (2 * paddingX={padding_x_interno}) = {block_width}px")
        
        return int(block_width)
    
    def _draw_product_block(self, draw, product, block_x_start, block_y_start, block_width, block_total_height, is_promotional):
        """
        Desenha um bloco de produto na imagem
        
        Args:
            draw (PIL.ImageDraw): Objeto de desenho
            product (dict): Dados do produto
            block_x_start (int): Posição X inicial do bloco
            block_y_start (int): Posição Y inicial do bloco
            block_width (int): Largura do bloco
            block_total_height (int): Altura total do bloco
            is_promotional (bool): Se é uma promoção
        """
        block_x_end = block_x_start + block_width
        block_y_end = block_y_start + block_total_height
        
        # Cores dinâmicas (do theme_config se disponível)
        if is_promotional:
            bg_color = self._get_promo_bg_color()
            text_color = self._get_promo_text_color()
        else:
            bg_color = self._get_normal_bg_color()
            text_color = self._get_normal_text_color()
        
        logger.info(f"      🔲 _draw_product_block: coords=({block_x_start},{block_y_start}) -> ({block_x_end},{block_y_end})")
        logger.info(f"      🎨 bg_color={bg_color}, text_color={text_color}, is_promo={is_promotional}")
        
        # Desenhar fundo do bloco
        draw.rectangle(
            [(block_x_start, block_y_start), (block_x_end, block_y_end)],
            fill=bg_color
        )
        logger.info(f"      ✅ Retângulo de fundo desenhado")
        
        # Inicializar cursor de posição Y para texto (usa padding interno vertical)
        padding_y_interno = self._get_bloco_padding_y()
        text_cursor_y = block_y_start + padding_y_interno
        
        # Dados do produto
        referencia = product['Referencia']
        descricao_final = product['DescricaoFinal']
        preco = product['Preco']
        preco_promocional = product['PrecoPromocional']
        preco_promocional_a_vista = product['PrecoPromocionalAVista']
        tamanhos_disponiveis = product['TamanhosDisponiveis']
        numeracao_utilizada_raw = product['NumeracaoUtilizada']
        
        # Formatar numeração utilizada - remover duplicação tipo "52 (52)"
        numeracao_utilizada = self._format_numeracao_utilizada(numeracao_utilizada_raw)
        
        # Helper para centralizar texto (com sombra se promocional)
        def draw_centered_text(text, y_pos, font, use_shadow=is_promotional):
            bbox = self._calculate_text_bbox(draw, text, font)
            text_width = bbox[2] - bbox[0]
            text_x = block_x_start + (block_width - text_width) / 2
            self._draw_text_with_shadow(draw, (text_x, y_pos), text, font, text_color, shadow=use_shadow)
            return bbox
        
        # Texto: Descrição Final (quebrar em até 2 linhas se necessário)
        reference_text = "Tam: ESGOTADO"
        bbox_ref = self._calculate_text_bbox(draw, reference_text, self.fonts['description'])
        max_width = bbox_ref[2] - bbox_ref[0]
        
        description_lines = self._split_description(descricao_final, max_width, self.fonts['description'], draw)
        for line in description_lines:
            bbox = draw_centered_text(line, text_cursor_y, self.fonts['description'])
            text_cursor_y += (bbox[3] - bbox[1]) * self._get_line_height()
        
        # Texto: Referência
        ref_text = f"Ref {referencia}"
        bbox = draw_centered_text(ref_text, text_cursor_y, self.fonts['description'])
        text_cursor_y += (bbox[3] - bbox[1]) * self._get_line_height()
        
        # Texto: Tamanhos Disponíveis (não numeração utilizada!)
        if tamanhos_disponiveis and tamanhos_disponiveis != 'N/A':
            tam_text = f"Tam: {tamanhos_disponiveis}"
            bbox = draw_centered_text(tam_text, text_cursor_y, self.fonts['description'])
            text_cursor_y += (bbox[3] - bbox[1]) * self._get_line_height()
        
        # Texto: Usei (numeração utilizada)
        usei_text = f"Usei: {numeracao_utilizada}"
        bbox = draw_centered_text(usei_text, text_cursor_y, self.fonts['description'])
        text_cursor_y += (bbox[3] - bbox[1]) * self._get_line_height()
        
        # Seção de Preço (centralizado)
        if preco_promocional > 0:
            # Linha 1: "DE" + "R$XX,XX" (riscado) + "POR" na mesma linha - fonte menor (description)
            de_text = "DE"
            preco_antigo_text = self._format_price_text(preco)
            por_text = "POR"
            
            # Calcular larguras usando fonte description (menor)
            de_bbox = self._calculate_text_bbox(draw, de_text, self.fonts['description'])
            preco_antigo_bbox = self._calculate_text_bbox(draw, preco_antigo_text, self.fonts['description'])
            por_bbox = self._calculate_text_bbox(draw, por_text, self.fonts['description'])
            de_width = de_bbox[2] - de_bbox[0]
            preco_antigo_width = preco_antigo_bbox[2] - preco_antigo_bbox[0]
            por_width = por_bbox[2] - por_bbox[0]
            spacing = 6  # Espaço entre palavras
            total_width = de_width + spacing + preco_antigo_width + spacing + por_width
            
            # Centralizar a linha completa
            line_x_start = block_x_start + (block_width - total_width) / 2
            
            # Desenhar "DE" (sem risco)
            self._draw_text_with_shadow(draw, (line_x_start, text_cursor_y), de_text, self.fonts['description'], text_color, shadow=is_promotional)
            
            # Desenhar "R$XX,XX" (com risco) - posição após "DE"
            preco_x = line_x_start + de_width + spacing
            self._draw_text_with_shadow(draw, (preco_x, text_cursor_y), preco_antigo_text, self.fonts['description'], text_color, shadow=is_promotional)
            
            # Desenhar linha riscada APENAS sobre o preço antigo
            strike_y = text_cursor_y + (preco_antigo_bbox[3] - preco_antigo_bbox[1]) / 2 - 1
            draw.line(
                [(preco_x, int(strike_y)), (preco_x + preco_antigo_width, int(strike_y))],
                fill=text_color,
                width=2
            )
            
            # Desenhar "POR" ao lado
            por_x = preco_x + preco_antigo_width + spacing
            self._draw_text_with_shadow(draw, (por_x, text_cursor_y), por_text, self.fonts['description'], text_color, shadow=is_promotional)
            
            text_cursor_y += (de_bbox[3] - de_bbox[1]) * self._get_line_height()
            
            # Linha 2: Preço promocional (no cartão)
            promo_text = f"{self._format_price_text(preco_promocional)} no cartão"
            bbox = draw_centered_text(promo_text, text_cursor_y, self.fonts['price'])
            text_cursor_y += (bbox[3] - bbox[1]) * self._get_line_height()
            
            # Linha 3: Preço à vista (última linha - não incrementa cursor)
            if preco_promocional_a_vista > 0:
                vista_text = f"{self._format_price_text(preco_promocional_a_vista)} à vista"
                draw_centered_text(vista_text, text_cursor_y, self.fonts['price'])
                # Não incrementar text_cursor_y - é a última linha
        else:
            # Preço normal (última linha - não incrementa cursor)
            price_text = self._format_price_text(preco)
            draw_centered_text(price_text, text_cursor_y, self.fonts['price'])
    
    def _draw_esgotado_flag(self, image, block_x_start, block_y_start, block_width, block_total_height):
        """
        Desenha a faixa "ESGOTADO" sobre o bloco do produto
        
        Args:
            image (PIL.Image): Imagem para desenhar
            block_x_start (int): Posição X do bloco
            block_y_start (int): Posição Y do bloco
            block_width (int): Largura do bloco
            block_total_height (int): Altura do bloco
        
        Returns:
            PIL.Image: Imagem com a faixa desenhada
        """
        try:
            strip_height = int(block_total_height / 4)
            
            # Criar imagem para a faixa
            strip_image = Image.new(
                "RGBA",
                (block_width, strip_height),
                config.COLOR_ESGOTADO_BACKGROUND
            )
            strip_draw = ImageDraw.Draw(strip_image)
            
            # Centralizar texto "ESGOTADO"
            esgotado_text = "ESGOTADO"
            bbox = self._calculate_text_bbox(strip_draw, esgotado_text, self.fonts['esgotado'])
            text_x = (strip_image.width - (bbox[2] - bbox[0])) / 2
            text_y = (strip_image.height - (bbox[3] - bbox[1])) / 2
            
            strip_draw.text(
                (text_x, text_y),
                esgotado_text,
                font=self.fonts['esgotado'],
                fill=(255, 255, 255, 255)
            )
            
            # Colar a faixa no centro vertical do bloco
            strip_y_pos = block_y_start + (block_total_height - strip_height) / 2
            image.paste(strip_image, (block_x_start, int(strip_y_pos)), strip_image)
            
            logger.info("Faixa 'ESGOTADO' desenhada")
            return image
        except Exception as e:
            logger.error(f"Erro ao desenhar faixa 'ESGOTADO': {e}")
            return image
    
    def _calculate_block_height(self, draw, product):
        """
        Calcula a altura necessária para renderizar um bloco de produto
        
        Args:
            draw (PIL.ImageDraw): Objeto de desenho
            product (dict): Dados do produto
        
        Returns:
            int: Altura total do bloco
        """
        padding_y_interno = self._get_bloco_padding_y()
        line_height = self._get_line_height()
        
        # Iniciar com padding superior
        height = padding_y_interno
        
        # Descrição (pode ter 1 ou 2 linhas)
        reference_text = "Tam: ESGOTADO"
        bbox_ref = self._calculate_text_bbox(draw, reference_text, self.fonts['description'])
        max_width = bbox_ref[2] - bbox_ref[0]
        
        description_lines = self._split_description(product['DescricaoFinal'], max_width, self.fonts['description'], draw)
        bbox = self._calculate_text_bbox(draw, "X", self.fonts['description'])
        text_height = bbox[3] - bbox[1]
        
        # Todas as linhas de descrição
        height += len(description_lines) * text_height * line_height
        
        # Referência
        ref_text = f"Ref {product['Referencia']}"
        bbox = self._calculate_text_bbox(draw, ref_text, self.fonts['description'])
        height += (bbox[3] - bbox[1]) * line_height
        
        # Tamanhos disponíveis (se houver)
        if product['TamanhosDisponiveis'] and product['TamanhosDisponiveis'] != 'N/A':
            tam_text = f"Tam: {product['TamanhosDisponiveis']}"
            bbox = self._calculate_text_bbox(draw, tam_text, self.fonts['description'])
            height += (bbox[3] - bbox[1]) * line_height
        
        # Usei (numeração utilizada) - formatada
        numeracao_formatada = self._format_numeracao_utilizada(product['NumeracaoUtilizada'])
        usei_text = f"Usei: {numeracao_formatada}"
        bbox = self._calculate_text_bbox(draw, usei_text, self.fonts['description'])
        height += (bbox[3] - bbox[1]) * line_height
        
        # Preço (múltiplas linhas se promoção)
        if product['PrecoPromocional'] > 0:
            # Linha 1: "DE XX POR" com fonte description (menor)
            bbox_desc = self._calculate_text_bbox(draw, "X", self.fonts['description'])
            height += (bbox_desc[3] - bbox_desc[1]) * line_height
            
            # Linha 2: preço no cartão
            bbox_price = self._calculate_text_bbox(draw, "X", self.fonts['price'])
            height += (bbox_price[3] - bbox_price[1]) * line_height
            
            # Linha 3 (última): preço à vista - SEM line_height (última linha)
            height += (bbox_price[3] - bbox_price[1])
        else:
            # Preço normal (última linha) - SEM line_height (última linha)
            bbox = self._calculate_text_bbox(draw, "X", self.fonts['price'])
            height += (bbox[3] - bbox[1])
        
        # Padding inferior (igual ao superior para simetria perfeita)
        height += padding_y_interno
        return int(round(height))
    
    def process_image(self, task_id, products_data, original_image_url, theme_url=None, generate_dual_version=False, layout_config=None, theme_config=None, desconto_a_vista=5):
        """
        Processa uma imagem com os dados de produtos
        Se generate_dual_version=True, processa 2 versões (com e sem tema)
        
        Args:
            task_id (str): ID único da tarefa
            products_data (list): Lista de produtos
            original_image_url (str): URL da imagem original
            theme_url (str): URL do tema (opcional)
            generate_dual_version (bool): Se deve gerar versão normal + promocional
            layout_config (dict): Configurações de layout (blocoX, blocoY, fontes, etc.)
            theme_config (dict): Configurações de tema (cores, fonte)
            desconto_a_vista (float): Percentual de desconto à vista (default 5%)
        
        Returns:
            str: Caminho do arquivo salvo ou None em caso de erro
        """
        # Aplicar configs dinâmicas
        self.layout_config = layout_config
        self.theme_config = theme_config
        self.desconto_a_vista = desconto_a_vista or 5
        
        # Recarregar fontes com tamanhos dinâmicos se layout_config foi fornecido
        if layout_config or theme_config:
            self.fonts = self._load_fonts_with_config(layout_config, theme_config)
            logger.info(f"   📐 Layout dinâmico aplicado: blocoX={self._get_bloco_x()}, blocoY={self._get_padding_y()}, spacing={self._get_block_spacing()}")
            logger.info(f"   📐 Padding interno: paddingX={self._get_padding_x()}, paddingY={self._get_bloco_padding_y()}")
            logger.info(f"   🎨 Cores dinâmicas aplicadas: promo_bg={self._get_promo_bg_color()}")
            logger.info(f"   💰 Desconto à vista: {self.desconto_a_vista}%")
        
        logger.info(f"========================================")
        logger.info(f"🚀 Iniciando processamento de imagem")
        logger.info(f"   Task ID: {task_id}")
        logger.info(f"   Produtos: {len(products_data)}")
        logger.info(f"   URL Original: {original_image_url}")
        logger.info(f"   URL Tema: {theme_url if theme_url else 'NENHUM TEMA FORNECIDO'}")
        logger.info(f"   Dupla versão: {'SIM (normal + promocional)' if generate_dual_version else 'NÃO (apenas normal)'}")
        logger.info(f"========================================")
        
        task_manager.update_task_status(task_id, "PROCESSING")
        
        try:
            # 1. Download da imagem original
            logger.info(f"📥 Baixando imagem original...")
            base_image = self._download_image(original_image_url)
            width, height = base_image.size
            logger.info(f"✅ Imagem original carregada: {width}x{height}")
            
            # 2. Preparar versões (com e sem tema)
            base_image_no_theme = None
            if generate_dual_version and theme_url:
                # Salvar cópia sem tema para versão normal
                base_image_no_theme = base_image.copy()
                logger.info(f"💾 Salvando cópia da imagem original (sem tema) para versão normal")
            
            # Aplicar tema (se fornecido e disponível)
            if theme_url:
                try:
                    logger.info(f"🎨 TEMA DETECTADO - Iniciando download...")
                    logger.info(f"   URL completa do tema: {theme_url}")
                    theme_image = self._download_image(theme_url)
                    logger.info(f"✅ Tema baixado com sucesso: {theme_image.size}")
                    base_image = self._apply_theme(base_image, theme_image)
                    logger.info(f"✅ TEMA APLICADO COM SUCESSO na imagem base")
                except Exception as e:
                    logger.warning(f"⚠️ FALHA ao aplicar tema: {e}")
                    logger.warning(f"⚠️ Continuando processamento sem tema - apenas blocos de produto")
            else:
                logger.warning("⚠️ NENHUM TEMA FORNECIDO - Processando apenas com overlay de blocos")
            
            # 3. Normalizar dados dos produtos
            normalized_products = []
            for product in products_data:
                try:
                    normalized_products.append(validate_product_data(product))
                except ValueError as e:
                    logger.error(f"Erro ao normalizar produto: {e}")
                    raise
            
            # 4. Criar imagem final com blocos de produtos
            # Se gerar dupla versão: processar NORMAL primeiro (todos produtos, sem tema)
            # Depois processar PROMOCIONAL (só produtos em oferta, com tema)
            
            # Verificar se há produtos promocionais
            has_promo = any(p['PrecoPromocional'] > 0 for p in normalized_products)
            
            if generate_dual_version and base_image_no_theme:
                logger.info(f"🎨 MODO DUPLO: Processando versão NORMAL (todos produtos, sem tema)...")
                
                # VERSÃO NORMAL: Base sem tema + TODOS os produtos
                final_image_normal = base_image_no_theme.copy()
                draw_normal = ImageDraw.Draw(final_image_normal)
                
                current_y_offset_normal = height - self._get_padding_y()
                
                # Calcular largura UNIFORME baseada em TODOS os produtos
                product_block_width_normal = self._calculate_uniform_block_width(draw_normal, normalized_products, check_promotional=True)
                logger.info(f"📏 Largura uniforme calculada (NORMAL): {product_block_width_normal}px para {len(normalized_products)} produtos")
                
                for idx, product in enumerate(reversed(normalized_products)):
                    is_promotional = product['PrecoPromocional'] > 0
                    block_height = self._calculate_block_height(draw_normal, product)
                    block_y_start = current_y_offset_normal - block_height
                    block_x_start = self._get_bloco_x()
                    
                    self._draw_product_block(
                        draw_normal,
                        product,
                        block_x_start,
                        block_y_start,
                        product_block_width_normal,
                        block_height,
                        is_promotional
                    )
                    
                    if product['Esgotado']:
                        final_image_normal = self._draw_esgotado_flag(
                            final_image_normal,
                            block_x_start,
                            block_y_start,
                            product_block_width_normal,
                            block_height
                        )
                        # Recriar draw após modificar imagem
                        draw_normal = ImageDraw.Draw(final_image_normal)
                    
                    current_y_offset_normal = block_y_start - self._get_block_spacing()
                
                # Salvar versão NORMAL
                output_filename_normal = f"{task_id}_normal.jpg"
                normal_path = os.path.join(config.TEMP_IMAGES_DIR, output_filename_normal)
                final_image_normal_rgb = final_image_normal.convert("RGB")
                final_image_normal_rgb.save(normal_path, "JPEG", quality=config.OUTPUT_IMAGE_QUALITY)
                logger.info(f"✅ Versão NORMAL salva: {normal_path} ({len(normalized_products)} produtos)")
                
                # VERSÃO PROMOCIONAL: Base com tema + APENAS produtos em oferta
                logger.info(f"🎁 Processando versão PROMOCIONAL (só produtos em oferta, com tema)...")
                
                # Filtrar apenas produtos promocionais
                promo_products = [p for p in normalized_products if p['PrecoPromocional'] > 0]
                
                if not promo_products:
                    logger.warning(f"⚠️ Nenhum produto promocional encontrado! Pulando versão promocional.")
                    final_path = normal_path  # Usar versão normal como padrão
                else:
                    # Criar uma nova imagem RGB a partir da base_image
                    # Não usar máscara alpha - simplesmente copiar os pixels visíveis
                    logger.info(f"   🔄 Preparando imagem para desenho (modo: {base_image.mode})...")
                    
                    # Compor base_image sobre fundo branco usando alpha_composite
                    if base_image.mode == 'RGBA':
                        background = Image.new("RGBA", base_image.size, (255, 255, 255, 255))
                        composite = Image.alpha_composite(background, base_image)
                        final_image_promo = composite.convert("RGB")
                        logger.info(f"   ✅ Imagem composta e convertida para RGB")
                    else:
                        final_image_promo = base_image.convert("RGB")
                        logger.info(f"   ✅ Imagem convertida para RGB diretamente")
                    
                    draw_promo = ImageDraw.Draw(final_image_promo)
                    
                    current_y_offset_promo = height - self._get_padding_y()
                    
                    # Calcular largura UNIFORME baseada apenas nos produtos promocionais
                    product_block_width_promo = self._calculate_uniform_block_width(draw_promo, promo_products, check_promotional=True)
                    
                    logger.info(f"   Processando {len(promo_products)} produto(s) promocional(is)")
                    logger.info(f"   📏 Largura uniforme (PROMO): {product_block_width_promo}px")
                    logger.info(f"   📏 Offset Y inicial: {current_y_offset_promo}px")
                    
                    for idx, product in enumerate(reversed(promo_products)):
                        block_height = self._calculate_block_height(draw_promo, product)
                        block_y_start = current_y_offset_promo - block_height
                        block_x_start = self._get_bloco_x()
                        
                        logger.info(f"   🎯 Desenhando produto {idx+1}: pos=({block_x_start}, {block_y_start}), altura={block_height}px")
                        
                        self._draw_product_block(
                            draw_promo,
                            product,
                            block_x_start,
                            block_y_start,
                            product_block_width_promo,
                            block_height,
                            True  # Sempre promocional
                        )
                        
                        logger.info(f"   ✅ Bloco do produto {idx+1} desenhado")
                        
                        if product['Esgotado']:
                            final_image_promo = self._draw_esgotado_flag(
                                final_image_promo,
                                block_x_start,
                                block_y_start,
                                product_block_width_promo,
                                block_height
                            )
                            # Recriar draw após modificar imagem
                            draw_promo = ImageDraw.Draw(final_image_promo)
                        
                        current_y_offset_promo = block_y_start - self._get_block_spacing()
                    
                    # Salvar versão PROMOCIONAL
                    output_filename_promo = f"{task_id}.jpg"
                    final_path = os.path.join(config.TEMP_IMAGES_DIR, output_filename_promo)
                    logger.info(f"   📷 [v2.1] Imagem promo antes de salvar: modo={final_image_promo.mode}, tamanho={final_image_promo.size}")
                    
                    # DEBUG: Salvar uma cópia de debug para verificar se a imagem está correta
                    debug_path = os.path.join(config.TEMP_IMAGES_DIR, f"DEBUG_{task_id}.jpg")
                    final_image_promo.save(debug_path, "JPEG", quality=95)
                    logger.info(f"   🐞 DEBUG: Imagem de debug salva em: {debug_path}")
                    
                    # Se ainda for RGBA (não deveria), converter para RGB
                    if final_image_promo.mode == 'RGBA':
                        rgb_image = Image.new("RGB", final_image_promo.size, (255, 255, 255))
                        rgb_image.paste(final_image_promo, mask=final_image_promo.split()[3])
                        final_image_promo = rgb_image
                    
                    logger.info(f"   📷 [v2.1] Salvando imagem final: modo={final_image_promo.mode}, path={final_path}")
                    final_image_promo.save(final_path, "JPEG", quality=config.OUTPUT_IMAGE_QUALITY)
                    
                    # Verificar se o arquivo foi salvo corretamente
                    import os as os_check
                    if os_check.path.exists(final_path):
                        file_size = os_check.path.getsize(final_path)
                        logger.info(f"✅ [v2.1] Versão PROMOCIONAL salva: {final_path} (tamanho: {file_size} bytes)")
                    else:
                        logger.error(f"❌ ERRO: Arquivo não foi salvo: {final_path}")
                
            else:
                # MODO SIMPLES: Processar normalmente com TODOS os produtos
                logger.info(f"📦 MODO SIMPLES: Processando imagem única...")
                
                final_image = base_image.copy()
                draw = ImageDraw.Draw(final_image)
                
                # Calcular espaço necessário e posições dos blocos
                current_y_offset = height - self._get_padding_y()
                
                # Calcular largura UNIFORME baseada em TODOS os produtos
                product_block_width = self._calculate_uniform_block_width(draw, normalized_products, check_promotional=True)
                logger.info(f"📏 Largura uniforme calculada: {product_block_width}px para {len(normalized_products)} produtos")
                
                for idx, product in enumerate(reversed(normalized_products)):
                    is_promotional = product['PrecoPromocional'] > 0
                    
                    # Calcular altura do bloco
                    block_height = self._calculate_block_height(draw, product)
                    
                    # Posicionar bloco
                    block_y_start = current_y_offset - block_height
                    block_x_start = self._get_bloco_x()
                    
                    # Desenhar bloco com cores padrão (preto ou vermelho se promoção)
                    self._draw_product_block(
                        draw,
                        product,
                        block_x_start,
                        block_y_start,
                        product_block_width,
                        block_height,
                        is_promotional
                    )
                    
                    # Desenhar flag "ESGOTADO" se necessário
                    if product['Esgotado']:
                        final_image = self._draw_esgotado_flag(
                            final_image,
                            block_x_start,
                            block_y_start,
                            product_block_width,
                            block_height
                        )
                        # Recriar draw após modificar imagem
                        draw = ImageDraw.Draw(final_image)
                    
                    # Atualizar offset para próximo bloco (usar BLOCK_SPACING entre blocos)
                    current_y_offset = block_y_start - self._get_block_spacing()
                
                # Salvar versão SIMPLES (FORA do loop - após processar TODOS os produtos)
                output_filename = f"{task_id}.jpg"
                final_path = os.path.join(config.TEMP_IMAGES_DIR, output_filename)
                final_image_rgb = final_image.convert("RGB")
                final_image_rgb.save(final_path, "JPEG", quality=config.OUTPUT_IMAGE_QUALITY)
                logger.info(f"✅ Imagem salva: {final_path} ({len(normalized_products)} produtos)")
                normal_path = None
            
            # Atualizar status da tarefa
            task_manager.update_task_status(
                task_id, 
                "COMPLETED", 
                final_path=final_path,
                normal_path=normal_path
            )
            
            return final_path
        
        except Exception as e:
            logger.error(f"Erro ao processar imagem para tarefa {task_id}: {e}", exc_info=True)
            task_manager.update_task_status(task_id, "FAILED", error_message=str(e))
            return None

# Instância global
image_processor = ImageProcessor()
