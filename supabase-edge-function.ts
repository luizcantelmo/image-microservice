// Supabase Edge Function - Exemplo de Integração
// Deploy em https://supabase.com/docs/guides/functions

import { serve } from "https://deno.land/std@0.200.0/http/server.ts";
import { corsHeaders } from "https://deno.land/std@0.168.0/http/cors.ts";

// Configurar variáveis de ambiente no console Supabase
const MICROSERVICE_URL = Deno.env.get("MICROSERVICE_URL") || "http://localhost:5001";
const MAX_POLLING_ATTEMPTS = 60;  // 2 minutos com 2s de intervalo
const POLLING_INTERVAL = 2000;    // 2 segundos

interface ProductData {
  Referencia: string;
  DescricaoFinal: string;
  Preco: number;
  PrecoPromocional: number;
  PrecoPromocionalAVista: number;
  TamanhosDisponiveis: string;
  NumeracaoUtilizada: string;
  Esgotado: boolean;
}

interface ProcessImageRequest {
  products: ProductData[];
  original_image_url: string;
  watermark_url?: string;
}

interface ProcessImageResponse {
  status: "completed" | "failed" | "timeout";
  image_url?: string;
  image_data?: string;  // Base64 se requested
  error?: string;
  task_id: string;
}

// Função auxiliar: polling de status
async function pollStatus(
  taskId: string,
  maxAttempts: number = MAX_POLLING_ATTEMPTS
): Promise<{
  status: string;
  final_image_url?: string;
  error_message?: string;
}> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const statusResponse = await fetch(
      `${MICROSERVICE_URL}/api/v1/status/${taskId}`
    );

    if (!statusResponse.ok) {
      throw new Error(`Status check failed: ${statusResponse.status}`);
    }

    const statusData = await statusResponse.json();

    if (
      statusData.status === "COMPLETED" ||
      statusData.status === "FAILED"
    ) {
      return statusData;
    }

    // Aguardar antes de proximar tentativa
    await new Promise((resolve) => setTimeout(resolve, POLLING_INTERVAL));
  }

  throw new Error(`Timeout ao processar imagem (${maxAttempts} tentativas)`);
}

// Função auxiliar: download da imagem
async function downloadImage(
  imageUrl: string,
  returnBase64: boolean = false
): Promise<string | Uint8Array> {
  const response = await fetch(`${MICROSERVICE_URL}${imageUrl}`);

  if (!response.ok) {
    throw new Error(`Failed to download image: ${response.status}`);
  }

  if (returnBase64) {
    const buffer = await response.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  } else {
    return await response.arrayBuffer();
  }
}

// Função principal da Edge Function
serve(async (req: Request) => {
  // Permitir CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Validar método
    if (req.method !== "POST") {
      return new Response(
        JSON.stringify({ error: "Método não permitido" }),
        {
          status: 405,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Parse do payload
    const payload: ProcessImageRequest = await req.json();

    // Validação básica
    if (
      !payload.products ||
      !Array.isArray(payload.products) ||
      payload.products.length === 0
    ) {
      return new Response(
        JSON.stringify({ error: "Campo 'products' obrigatório e não vazio" }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    if (!payload.original_image_url) {
      return new Response(
        JSON.stringify({
          error: "Campo 'original_image_url' obrigatório",
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    console.log(
      `Processando imagem com ${payload.products.length} produto(s)...`
    );

    // Enviar para microserviço
    const processResponse = await fetch(
      `${MICROSERVICE_URL}/api/v1/process-image`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          products: payload.products,
          original_image_url: payload.original_image_url,
          watermark_url: payload.watermark_url || null,
        }),
      }
    );

    if (!processResponse.ok) {
      const errorData = await processResponse.json();
      return new Response(JSON.stringify({ error: errorData.error }), {
        status: processResponse.status,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const processData = await processResponse.json();
    const taskId = processData.task_id;

    console.log(`Task ID: ${taskId} - Iniciando polling...`);

    // Polling até conclusão
    let statusData = await pollStatus(taskId);

    if (statusData.status === "FAILED") {
      return new Response(
        JSON.stringify({
          status: "failed",
          error: statusData.error_message,
          task_id: taskId,
        }),
        {
          status: 200,  // Retornar 200 mesmo com erro, apenas status diferente
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Fazer download da imagem
    console.log(`Imagem pronta! Baixando...`);
    const imageUrl = statusData.final_image_url;

    // Opção 1: Retornar URL (cliente faz download)
    const response: ProcessImageResponse = {
      status: "completed",
      image_url: `${MICROSERVICE_URL}${imageUrl}`,
      task_id: taskId,
    };

    // Opção 2: Retornar Base64 (se tamanho < 6MB)
    // Descomente para retornar imagem embarcada
    /*
    try {
      const imageBase64 = await downloadImage(imageUrl, true);
      response.image_data = imageBase64 as string;
    } catch (e) {
      console.warn("Não foi possível retornar imagem em Base64:", e);
    }
    */

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error) {
    console.error("Erro ao processar imagem:", error);

    return new Response(
      JSON.stringify({
        status: "failed",
        error: `Erro interno: ${error.message}`,
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});

/* 
========== DEPLOY NO SUPABASE ==========

1. Crie a function no console Supabase:
   supabase functions create image-processing

2. Substitua o conteúdo de supabase/functions/image-processing/index.ts

3. Configure variáveis de ambiente:
   supabase secrets set MICROSERVICE_URL=https://seu.dominio.com

4. Deploy:
   supabase functions deploy image-processing

5. Obtenha a URL (aparece na saída):
   https://seu-projeto.supabase.co/functions/v1/image-processing

6. Use no cliente:
   const response = await fetch(
     'https://seu-projeto.supabase.co/functions/v1/image-processing',
     {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         products: [...],
         original_image_url: "...",
         watermark_url: "..."
       })
     }
   );
   const data = await response.json();
   console.log(data);

========== EXEMPLO DE USO NO CLIENTE ==========

// Client-side (JavaScript/TypeScript)

async function processProductImage(products, imageUrl, watermarkUrl) {
  const response = await fetch(
    'https://seu-projeto.supabase.co/functions/v1/image-processing',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseClient.auth.session().access_token}`  // Opcional
      },
      body: JSON.stringify({
        products: products,
        original_image_url: imageUrl,
        watermark_url: watermarkUrl
      })
    }
  );

  if (!response.ok) {
    throw new Error(`Erro ao processar: ${response.status}`);
  }

  const result = await response.json();
  
  if (result.status === 'completed') {
    console.log('Imagem processada! URL:', result.image_url);
    // Usar result.image_url ou result.image_data (base64)
    return result.image_url;
  } else {
    throw new Error(`Processamento falhou: ${result.error}`);
  }
}

// Uso:
const imageUrl = await processProductImage(
  [
    {
      Referencia: 'REF-001',
      DescricaoFinal: 'Camiseta Premium',
      Preco: 99.90,
      PrecoPromocional: 79.90,
      PrecoPromocionalAVista: 75.90,
      TamanhosDisponiveis: 'P, M, G',
      NumeracaoUtilizada: 'M',
      Esgotado: false
    }
  ],
  'https://example.com/image.jpg',
  'https://example.com/logo.png'
);

*/
