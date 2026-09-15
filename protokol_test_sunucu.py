#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KATI PROTOKOL TAKLİTÇİSİ

Amaç: "çalışıyor" demek yetmez — HANGİ protokolle çalıştığını kanıtlamak
gerekir. Bu sunucular yanlış protokolü REDDEDER:

  anthropic modu · yalnız  POST /v1/messages
                   başlık  x-api-key + anthropic-version
                   gövde   {model, max_tokens, system, messages}
                   yanıt   {content:[{type:"text",text:…}], stop_reason}

  openai modu    · yalnız  POST /v1/chat/completions
                   başlık  Authorization: Bearer …
                   gövde   {model, messages:[{role:"system"|…}]}
                   yanıt   {choices:[{message:{content},finish_reason}]}

Yanlış yola ya da yanlış başlıkla gelen istek 400/401 alır. Böylece
kodun gerçekten doğru protokolü konuştuğu kanıtlanır, sadece "200 döndü"
denmiş olmaz.
"""
import json
import sys
import http.server
import socketserver

PORT = int(sys.argv[1])
MOD = sys.argv[2]                      # anthropic | openai
KAYIT = f"/tmp/protokol_{MOD}_{PORT}.log"


def yaz(satir: str) -> None:
    with open(KAYIT, "a", encoding="utf-8") as f:
        f.write(satir + "\n")


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, kod: int, govde: dict) -> None:
        self.send_response(kod)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(govde).encode())

    def do_GET(self):
        if MOD == "anthropic":
            # Anthropic'in model listesi ucu /v1/models
            if self.path != "/v1/models":
                yaz(f"GET RED yol={self.path}")
                return self._json(404, {"error": "yol yok"})
            if not self.headers.get("x-api-key"):
                yaz("GET RED x-api-key yok")
                return self._json(401, {"error": "x-api-key gerekli"})
            yaz(f"GET OK {self.path}")
            return self._json(200, {"data": [{"id": "claude-sonnet-4-6"}]})
        # openai
        if self.path != "/v1/models":
            yaz(f"GET RED yol={self.path}")
            return self._json(404, {"error": "yol yok"})
        if not (self.headers.get("Authorization") or "").startswith("Bearer "):
            yaz("GET RED Bearer yok")
            return self._json(401, {"error": "Bearer gerekli"})
        yaz(f"GET OK {self.path}")
        return self._json(200, {"data": [{"id": "gpt-4o"}]})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            g = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            g = {}

        if MOD == "anthropic":
            if self.path != "/v1/messages":
                yaz(f"POST RED yanlış yol: {self.path}")
                return self._json(404, {"error": {"message": "yol yok"}})
            if not self.headers.get("x-api-key"):
                yaz("POST RED x-api-key yok")
                return self._json(401, {"error": {"message": "x-api-key gerekli"}})
            if not self.headers.get("anthropic-version"):
                yaz("POST RED anthropic-version yok")
                return self._json(400, {"error": {"message": "sürüm başlığı yok"}})
            if "max_tokens" not in g:
                yaz("POST RED max_tokens yok")
                return self._json(400, {"error": {"message": "max_tokens zorunlu"}})
            # Anthropic'te system AYRI alandır, messages içinde olmaz
            if any(m.get("role") == "system" for m in g.get("messages", [])):
                yaz("POST RED system messages içinde")
                return self._json(400, {"error": {"message": "system ayrı olmalı"}})
            yaz(f"POST OK /v1/messages model={g.get('model')} "
                f"system={'var' if g.get('system') else 'yok'} "
                f"mesaj={len(g.get('messages', []))}")
            return self._json(200, {
                "content": [{"type": "text", "text": "[ANTHROPIC] yanıt"}],
                "stop_reason": "end_turn", "model": g.get("model")})

        # openai
        if self.path != "/v1/chat/completions":
            yaz(f"POST RED yanlış yol: {self.path}")
            return self._json(404, {"error": {"message": "yol yok"}})
        if not (self.headers.get("Authorization") or "").startswith("Bearer "):
            yaz("POST RED Bearer yok")
            return self._json(401, {"error": {"message": "Bearer gerekli"}})
        # OpenAI'de system messages İÇİNDE olur
        if not any(m.get("role") == "system" for m in g.get("messages", [])):
            yaz("POST RED system messages içinde değil")
            return self._json(400, {"error": {"message": "system mesajı yok"}})
        yaz(f"POST OK /v1/chat/completions model={g.get('model')} "
            f"mesaj={len(g.get('messages', []))}")
        return self._json(200, {
            "choices": [{"message": {"content": "[OPENAI] yanıt"},
                         "finish_reason": "stop"}],
            "model": g.get("model")})


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), H) as s:
    s.serve_forever()
