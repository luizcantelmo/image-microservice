# Plano: Upload Duplo para Produtos Promocionais

## Objetivo
Quando um produto estiver em promoção:
1. Salvar **versão SEM tema promocional** no diretório calculado normal
2. Salvar **versão COM tema promocional** no diretório "PROMOCAO" (raiz do Drive)

## Alterações Necessárias

### 1. Configurações do Supabase
Adicionar na tabela `configuracoes`:
```sql
INSERT INTO configuracoes (chave, valor, descricao) VALUES 
('GOOGLE_DRIVE_PASTA_PROMOCAO_ID', '1Tym3Iud3kfzxU441_ZJgPZ_2dZjy6oDL', 'ID da pasta PROMOCAO no Google Drive');
```

### 2. Microservice (image-microservice)

#### 2.1. Endpoint `/api/v1/process-image`
Modificar para retornar **2 buffers** quando `has_promotional`:
```python
# Em app/main.py
@app.route('/api/v1/process-image', methods=['POST'])
def process_image_request():
    # ... código existente ...
    
    # Verificar se há produtos promocionais
    has_promo = any(p.get('PrecoPromocional', 0) > 0 for p in products_data)
    
    if has_promo:
        # Processar 2 versões
        version_normal = processor.process_image(task_id, products_data, image_url, theme_url=None)
        version_promo = processor.process_image(task_id, products_data, image_url, theme_url=theme_url)
        
        return jsonify({
            'task_id': task_id,
            'status': 'COMPLETED',
            'images': {
                'normal': base64.b64encode(version_normal).decode(),
                'promotional': base64.b64encode(version_promo).decode()
            }
        })
    else:
        # Processar apenas 1 versão normal
        # ... código atual ...
```

#### 2.2. image_processor.py
Modificar `process_image()` para aceitar parâmetro `apply_theme`:
```python
def process_image(self, task_id, products_data, original_image_url, theme_url=None, apply_theme=True):
    # ...
    
    # 2. Aplicar tema apenas se apply_theme=True
    if theme_url and apply_theme:
        # ... código atual de aplicação de tema ...
    
    # ... resto do processamento ...
```

### 3. Edge Function (process-product-image)

#### 3.1. Buscar ID da pasta PROMOCAO
```typescript
// Após linha ~1630
const { data: configPromo } = await supabaseAdmin
  .from('configuracoes')
  .select('valor')
  .eq('chave', 'GOOGLE_DRIVE_PASTA_PROMOCAO_ID')
  .single();

const promocaoPastaId = configPromo?.valor || null;
```

#### 3.2. Processar resposta do microservice
```typescript
// Após processamento do microservice (~linha 1670)
let processedImageBuffer: Uint8Array;
let processedImagePromoBuffer: Uint8Array | null = null;

if (result.images) {
  // Microservice retornou 2 versões
  processedImageBuffer = Uint8Array.from(atob(result.images.normal), c => c.charCodeAt(0));
  processedImagePromoBuffer = Uint8Array.from(atob(result.images.promotional), c => c.charCodeAt(0));
} else {
  // Retrocompatibilidade: apenas 1 versão
  processedImageBuffer = new Uint8Array(result.processed_image_buffer);
}
```

#### 3.3. Upload duplo
```typescript
// No loop de upload (~linha 1715)
for (const info of produtosInfo) {
  // Upload normal no diretório calculado
  const uploadResult = await uploadToGoogleDrive(
    info.fileName,
    processedImageBuffer,
    info.googleDriveParentFolderId!,
    googleAccessToken
  );
  
  // Se tiver versão promocional E pasta PROMOCAO configurada
  if (processedImagePromoBuffer && promocaoPastaId && info.precoPromocional > 0) {
    const promoFileName = `PROMO_${info.fileName}`;
    const uploadPromoResult = await uploadToGoogleDrive(
      promoFileName,
      processedImagePromoBuffer,
      promocaoPastaId,
      googleAccessToken
    );
    
    console.log(`✅ Versão promocional salva: ${uploadPromoResult.webViewLink}`);
    
    // Opcional: salvar link da versão promocional no banco
    await supabaseAdmin.from('produtos_fotos').update({
      path_promocional: uploadPromoResult.webViewLink,
      google_drive_promo_file_id: uploadPromoResult.id
    }).eq('id', info.produtoFotoId);
  }
}
```

### 4. Schema do Banco (Opcional)
Adicionar colunas em `produtos_fotos`:
```sql
ALTER TABLE produtos_fotos 
ADD COLUMN path_promocional TEXT,
ADD COLUMN google_drive_promo_file_id TEXT;
```

## Status Atual
✅ **Implementado:**
- Sombra de texto em produtos promocionais (melhor legibilidade)
- Largura dinâmica do bloco calculada para acomodar "POR R$119,90 no cartão"
- Cor crimson menos saturada (220, 20, 60) em vez de vermelho puro
- Opacidade aumentada (220 vs 200)

⏳ **Pendente:**
- Configurar ID da pasta PROMOCAO no Supabase
- Modificar microservice para retornar 2 versões
- Modificar Edge Function para fazer upload duplo
- Testar fluxo completo

## Próximos Passos
1. Criar pasta "PROMOCAO" no Google Drive raiz
2. Adicionar ID na tabela configuracoes
3. Implementar alterações no microservice
4. Implementar alterações na Edge Function
5. Testar com produto promocional
6. Validar ambas as fotos nos diretórios corretos
