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
    
    def _format_price_text(self, price):
        """Formata preço para formato brasileiro (R$ X.XXX,XX)"""
        return f"R${price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
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
        
        # Selecionar cores
        if is_promotional:
            background_color = config.COLOR_PROMO_BACKGROUND
            text_color = config.COLOR_TEXT_WHITE
        else:
            background_color = config.COLOR_NORMAL_BACKGROUND
            text_color = config.COLOR_TEXT_WHITE
        
        # Desenhar fundo do bloco
        draw.rectangle(
            [(block_x_start, block_y_start), (block_x_end, block_y_end)],
            fill=background_color
        )
        
        # Inicializar cursor de posição Y para texto
        text_cursor_y = block_y_start + 10  # Padding superior reduzido
        
        # Dados do produto
        referencia = product['Referencia']
        descricao_final = product['DescricaoFinal']
        preco = product['Preco']
        preco_promocional = product['PrecoPromocional']
        preco_promocional_a_vista = product['PrecoPromocionalAVista']
        tamanhos_disponiveis = product['TamanhosDisponiveis']
        numeracao_utilizada = product['NumeracaoUtilizada']
        
        # Helper para centralizar texto
        def draw_centered_text(text, y_pos, font):
            bbox = self._calculate_text_bbox(draw, text, font)
            text_width = bbox[2] - bbox[0]
            text_x = block_x_start + (block_width - text_width) / 2
            draw.text((text_x, y_pos), text, font=font, fill=text_color)
            return bbox
        
        # Texto: Descrição Final (truncar se muito longa)
        descricao_truncada = descricao_final[:20] if len(descricao_final) > 20 else descricao_final
        bbox = draw_centered_text(descricao_truncada, text_cursor_y, self.fonts['description'])
        text_cursor_y += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Texto: Referência
        ref_text = f"Ref {referencia}"
        bbox = draw_centered_text(ref_text, text_cursor_y, self.fonts['description'])
        text_cursor_y += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Texto: Tamanhos Disponíveis (não numeração utilizada!)
        if tamanhos_disponiveis and tamanhos_disponiveis != 'N/A':
            tam_text = f"Tam: {tamanhos_disponiveis}"
            bbox = draw_centered_text(tam_text, text_cursor_y, self.fonts['description'])
            text_cursor_y += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Texto: Usei (numeração utilizada)
        usei_text = f"Usei: {numeracao_utilizada}"
        bbox = draw_centered_text(usei_text, text_cursor_y, self.fonts['description'])
        text_cursor_y += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Seção de Preço (centralizado)
        if preco_promocional > 0:
            # Preço "DE" (riscado)
            de_text = f"DE {self._format_price_text(preco)}"
            bbox = self._calculate_text_bbox(draw, de_text, self.fonts['price'])
            text_width = bbox[2] - bbox[0]
            text_x = block_x_start + (block_width - text_width) / 2
            draw.text((text_x, text_cursor_y), de_text, font=self.fonts['price'], fill=text_color)
            
            # Desenhar linha riscada
            strike_y = text_cursor_y + (bbox[3] - bbox[1]) / 2 - 2
            draw.line(
                [(text_x, int(strike_y)), (text_x + text_width, int(strike_y))],
                fill=text_color,
                width=2
            )
            text_cursor_y += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
            
            # Preço promocional (no cartão)
            promo_text = f"POR {self._format_price_text(preco_promocional)} cartão"
            bbox = draw_centered_text(promo_text, text_cursor_y, self.fonts['price'])
            text_cursor_y += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
            
            # Preço à vista
            if preco_promocional_a_vista > 0:
                vista_text = f"{self._format_price_text(preco_promocional_a_vista)} à vista"
                draw_centered_text(vista_text, text_cursor_y, self.fonts['price'])
        else:
            # Preço normal
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
        height = 10  # Padding superior reduzido
        
        # Descrição
        bbox = self._calculate_text_bbox(draw, product['DescricaoFinal'][:20], self.fonts['description'])
        height += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Referência
        ref_text = f"Ref {product['Referencia']}"
        bbox = self._calculate_text_bbox(draw, ref_text, self.fonts['description'])
        height += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Tamanhos disponíveis (se houver)
        if product['TamanhosDisponiveis'] and product['TamanhosDisponiveis'] != 'N/A':
            tam_text = f"Tam: {product['TamanhosDisponiveis']}"
            bbox = self._calculate_text_bbox(draw, tam_text, self.fonts['description'])
            height += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Usei (numeração utilizada)
        usei_text = f"Usei: {product['NumeracaoUtilizada']}"
        bbox = self._calculate_text_bbox(draw, usei_text, self.fonts['description'])
        height += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        # Preço (múltiplas linhas se promoção)
        if product['PrecoPromocional'] > 0:
            # 3 linhas de preço
            bbox = self._calculate_text_bbox(draw, "X", self.fonts['price'])
            height += 3 * (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        else:
            bbox = self._calculate_text_bbox(draw, "X", self.fonts['price'])
            height += (bbox[3] - bbox[1]) * config.LINE_HEIGHT_MULTIPLIER
        
        return int(height + 10)  # Padding inferior reduzido
    
    def process_image(self, task_id, products_data, original_image_url, theme_url=None):
        """
        Processa uma imagem com os dados de produtos
        
        Args:
            task_id (str): ID único da tarefa
            products_data (list): Lista de produtos
            original_image_url (str): URL da imagem original
            theme_url (str): URL do tema (opcional)
        
        Returns:
            str: Caminho do arquivo salvo ou None em caso de erro
        """
        logger.info(f"========================================")
        logger.info(f"🚀 Iniciando processamento de imagem")
        logger.info(f"   Task ID: {task_id}")
        logger.info(f"   Produtos: {len(products_data)}")
        logger.info(f"   URL Original: {original_image_url}")
        logger.info(f"   URL Tema: {theme_url if theme_url else 'NENHUM TEMA FORNECIDO'}")
        logger.info(f"========================================")
        
        task_manager.update_task_status(task_id, "PROCESSING")
        
        try:
            # 1. Download da imagem original
            logger.info(f"📥 Baixando imagem original...")
            base_image = self._download_image(original_image_url)
            width, height = base_image.size
            logger.info(f"✅ Imagem original carregada: {width}x{height}")
            
            # 2. Aplicar tema se fornecido
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
                    logger.warning(f"⚠️ Continuando processamento sem tema")
            else:
                logger.warning("⚠️ NENHUM TEMA FORNECIDO - Processando apenas com overlay de texto")
                logger.warning("⚠️ Verifique se theme_url/watermark_url está sendo enviado corretamente")
            
            # 3. Normalizar dados dos produtos
            normalized_products = []
            for product in products_data:
                try:
                    normalized_products.append(validate_product_data(product))
                except ValueError as e:
                    logger.error(f"Erro ao normalizar produto: {e}")
                    raise
            
            # 4. Criar imagem final com todos os blocos de produtos
            final_image = base_image.copy()
            draw = ImageDraw.Draw(final_image)
            
            # Calcular espaço necessário e posições dos blocos
            current_y_offset = height - config.PADDING_Y
            product_block_width = int(width * config.PRODUCT_BLOCK_WIDTH_PERCENT)
            
            for product in reversed(normalized_products):
                is_promotional = product['PrecoPromocional'] > 0
                
                # Calcular altura do bloco
                block_height = self._calculate_block_height(draw, product)
                
                # Posicionar bloco
                block_y_start = current_y_offset - block_height
                block_x_start = config.PADDING_X
                
                # Desenhar bloco
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
                
                # Atualizar offset para próximo bloco
                current_y_offset = block_y_start - config.PADDING_Y
            
            # 5. Salvar imagem final
            output_filename = f"{task_id}.jpg"
            final_path = os.path.join(config.TEMP_IMAGES_DIR, output_filename)
            
            final_image_rgb = final_image.convert("RGB")
            final_image_rgb.save(final_path, "JPEG", quality=config.OUTPUT_IMAGE_QUALITY)
            
            logger.info(f"Imagem salva com sucesso: {final_path}")
            task_manager.update_task_status(task_id, "COMPLETED", final_path=final_path)
            
            return final_path
        
        except Exception as e:
            logger.error(f"Erro ao processar imagem para tarefa {task_id}: {e}", exc_info=True)
            task_manager.update_task_status(task_id, "FAILED", error_message=str(e))
            return None

# Instância global
image_processor = ImageProcessor()
