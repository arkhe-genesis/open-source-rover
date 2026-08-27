// src/hyperdrive.ts
export interface Env {
  HYPERDRIVE: Hyperdrive;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Authentication check required for sensitive endpoints
    const authHeader = request.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return new Response('Unauthorized', { status: 401 });
    }

    if (url.pathname === '/api/sql/query' && request.method === 'POST') {
      // Security measure: Do not accept arbitrary SQL queries from clients.
      // Implementing predefined parameterized queries is necessary here to prevent SQL injection.
      return new Response('Arbitrary SQL execution is not allowed', { status: 403 });
    }

    // Endpoint para obter métricas do projeto
    if (url.pathname === '/api/metrics') {
      const rows = await env.HYPERDRIVE.query(
        `SELECT * FROM vw_ProjectSummary WHERE ProjectID = $1`,
        [url.searchParams.get('projectId')]
      );
      return Response.json(rows);
    }

    return new Response('Not found', { status: 404 });
  }
};
