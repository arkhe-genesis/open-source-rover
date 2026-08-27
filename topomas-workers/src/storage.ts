// src/storage.ts
export interface Env {
  R2_BUCKET: R2Bucket;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Upload de artefato (ex: estrutura cristalina)
    if (url.pathname === '/api/upload' && request.method === 'POST') {
      const authHeader = request.headers.get('Authorization');
      if (!authHeader?.startsWith('Bearer ')) {
        return new Response('Unauthorized', { status: 401 });
      }

      const formData = await request.formData();
      const file = formData.get('file') as File;
      const key = formData.get('key') as string;

      // Ensure that files can only be uploaded to specific, safe directories
      // and do not overwrite critical system files.
      if (!key.startsWith('uploads/')) {
        return new Response('Invalid upload key prefix', { status: 403 });
      }

      await env.R2_BUCKET.put(key, file.stream(), {
        httpMetadata: { contentType: file.type }
      });
      return Response.json({ success: true, key });
    }

    // Download de artefato
    if (url.pathname.startsWith('/api/download/')) {
      const key = url.pathname.replace('/api/download/', '');
      const object = await env.R2_BUCKET.get(key);
      if (!object) {
        return new Response('Not found', { status: 404 });
      }
      return new Response(object.body, {
        headers: { 'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream' }
      });
    }

    return new Response('Not found', { status: 404 });
  }
};
