/**
 * Cloudflare Worker that forwards Plaid webhook requests to the backend.
 *
 * Set the `BACKEND_URL` environment variable to your backend's public URL
 * (e.g., your Render deployment). Deploy this worker on the route
 * `/api/webhooks/plaid` so Plaid's webhook traffic hits Cloudflare first
 * and is then relayed to your backend.
 */
export default {
  async fetch(request, env) {
    const backendBase = env.BACKEND_URL;
    if (!backendBase) {
      return new Response("BACKEND_URL not configured", { status: 500 });
    }

    const target = `${backendBase.replace(/\/$/, "")}/api/webhooks/plaid`;
    const init = {
      method: request.method,
      headers: request.headers,
      body: request.body,
    };

    try {
      const resp = await fetch(target, init);
      return resp;
    } catch (err) {
      return new Response("Error forwarding webhook", { status: 502 });
    }
  },
};
